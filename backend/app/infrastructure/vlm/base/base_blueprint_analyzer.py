from app.domain.entities.blueprint import Blueprint
from app.domain.value_objects.design_step import DesignStep
from app.domain.interfaces.blueprint_analyzer import IBlueprintAnalyzer
from abc import abstractmethod
import base64
import io
import json
import re
from typing import List
from loguru import logger

MAX_IMAGE_BYTES = 4 * 1024 * 1024  # 4MB（API上限5MBに余裕を持たせる）

class BaseBlueprintAnalyzer(IBlueprintAnalyzer):

    def _convert_pdf_to_image(self, file_path: str) -> bytes:
        """PDFの1ページ目をPNG画像のバイト列に変換する"""
        from pdf2image import convert_from_path
        images = convert_from_path(file_path, first_page=1, last_page=1, dpi=300)
        buf = io.BytesIO()
        images[0].save(buf, format="PNG")
        return buf.getvalue()

    def _compress_image(self, image_bytes: bytes, mime_type: str) -> tuple[bytes, str]:
        """画像がMAX_IMAGE_BYTESを超える場合、JPEG変換・リサイズで圧縮する"""
        if len(image_bytes) <= MAX_IMAGE_BYTES:
            return image_bytes, mime_type

        from PIL import Image

        img = Image.open(io.BytesIO(image_bytes))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        # 段階的にリサイズして4MB以下に収める
        quality = 85
        scale = 1.0
        for _ in range(5):
            buf = io.BytesIO()
            resized = img.resize(
                (int(img.width * scale), int(img.height * scale)),
                Image.LANCZOS,
            ) if scale < 1.0 else img
            resized.save(buf, format="JPEG", quality=quality)
            compressed = buf.getvalue()
            if len(compressed) <= MAX_IMAGE_BYTES:
                logger.info(
                    f"画像を圧縮: {len(image_bytes)} -> {len(compressed)} bytes "
                    f"(scale={scale:.2f}, quality={quality})"
                )
                return compressed, "image/jpeg"
            scale *= 0.75
            quality = max(quality - 10, 50)

        logger.warning(f"圧縮後も {len(compressed)} bytes — そのまま送信します")
        return compressed, "image/jpeg"

    def _encode_image(self, file_path: str, content_type: str) -> tuple[str, str]:
        """画像をbase64エンコードし、(base64データ, MIMEタイプ) を返す"""
        if content_type == "application/pdf":
            image_bytes = self._convert_pdf_to_image(file_path)
        else:
            with open(file_path, "rb") as f:
                image_bytes = f.read()

        image_bytes, mime_type = self._compress_image(image_bytes, content_type)
        return base64.b64encode(image_bytes).decode("utf-8"), mime_type

    @staticmethod
    def _extract_json(content: str) -> str:
        """LLM の応答から JSON 文字列を抽出する。

        対応する形式:
        - 素の JSON
        - ```json ... ``` でラップされた JSON
        - ``` ... ``` でラップされた JSON
        - 思考テキストの後ろに JSON が続く形式（最初の { から最後の } まで）
        """
        fence_match = re.search(r"```(?:json)?\s*\n(.*?)```", content, re.DOTALL)
        if fence_match:
            return fence_match.group(1).strip()

        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1 and end > start:
            return content[start : end + 1]

        return content.strip()

    def _parse_response(self, content: str) -> List[DesignStep]:
        json_text = self._extract_json(content)
        data = json.loads(json_text)

        clarifications = data.get("clarifications_needed", [])
        if clarifications:
            logger.warning(
                f"VLM が {len(clarifications)} 件の確認事項を報告しました: {clarifications}"
            )

        return [
            DesignStep(
                step_number=step["step_number"],
                instruction=step["instruction"],
            )
            for step in data["steps"]
        ]

    def _build_system_prompt(self) -> str:
        return """あなたは機械設計・CADの専門家です。与えられた2D図面画像を分析し、CadQueryで3Dモデルを作成するための手順を自然言語でステップバイステップに記述してください。

## 内部思考の手順（出力前に必ずこの順で検討すること）
1. 視点種別の判定：三面図 / 等角図 / 部分図 / 混在 のいずれか
2. 各ビューから読み取れる特徴をリストアップ（寸法線は別扱い）
3. 寸法の役割分類：直径 / 幅 / 深さ / 位置 / 公差 のいずれか
4. 座標系の確定：原点・基準面・Up方向
5. プライマリ形状の選定：押し出し / 回転 / スイープ
6. セカンダリ特徴の適用順序：穴 → 面取り → フィレット

## 出力フォーマット
以下のJSON形式で出力してください:
{
  "clarifications_needed": [
    "図面から読み取れない寸法や曖昧な指定があれば、ユーザーへの質問文として記載"
  ],
  "steps": [
    {"step_number": 1, "instruction": "手順の説明"},
    {"step_number": 2, "instruction": "手順の説明"}
  ]
}

## 座標系の定義
- 原点 (0, 0, 0) をモデルの底面中心に配置する
- X軸: 幅方向（左右）、Y軸: 奥行き方向（前後）、Z軸: 高さ方向（上下）
- CadQuery のデフォルト Workplane "XY" を基準面とする

## 注意事項
- instruction には具体的な寸法（mm単位の数値）、形状名、位置関係を必ず含めること
- 位置はベース形状の原点からの相対座標で記述すること（例: 「中心から X方向に +20mm の位置」）
- 各ステップは1つのモデリング操作に対応させること（例: 押し出し、穴あけ、面取りはそれぞれ別ステップ）
- step_number は 1 から始まる連番
- ステップ1は必ずベースとなるプリミティブ形状（直方体、円柱等）の作成とすること
- fillet や chamfer を指定する場合は、対象エッジの位置と半径を明記すること

## 不明寸法の扱い（厳守）
- 図面に記載のない寸法は推測で埋めない。`clarifications_needed` にユーザーへの質問として記載すること
- 例外：形状成立に必須かつ慣習的な値（例：標準フィレット半径 R1、面取り C0.5 等）が明らかな場合のみ推定可
- その場合は instruction の末尾に `(推定値)` と明記すること
- 質問が無い場合でも `clarifications_needed: []` として必ずフィールドを出力すること"""

    def analyze(self, blueprint: Blueprint) -> List[DesignStep]:
        image_data, mime_type = self._encode_image(blueprint.file_path, blueprint.content_type)
        content = self._call_api(image_data, mime_type)
        return self._parse_response(content)

    @abstractmethod
    def _call_api(self, image_data: str, mime_type: str) -> str:
        """LLM API を呼び出し、JSON 文字列を返す"""
        pass
        
