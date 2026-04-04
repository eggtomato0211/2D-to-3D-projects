from app.domain.entities.blueprint import Blueprint
from app.domain.value_objects.design_step import DesignStep
from app.domain.interfaces.blueprint_analyzer import IBlueprintAnalyzer
from abc import abstractmethod
import base64
import io
import json
from typing import List

class BaseBlueprintAnalyzer(IBlueprintAnalyzer):

    def _convert_pdf_to_image(self, file_path: str) -> bytes:
        """PDFの1ページ目をPNG画像のバイト列に変換する"""
        from pdf2image import convert_from_path
        images = convert_from_path(file_path, first_page=1, last_page=1, dpi=300)
        buf = io.BytesIO()
        images[0].save(buf, format="PNG")
        return buf.getvalue()

    def _encode_image(self, file_path: str, content_type: str) -> tuple[str, str]:
        """画像をbase64エンコードし、(base64データ, MIMEタイプ) を返す"""
        if content_type == "application/pdf":
            image_bytes = self._convert_pdf_to_image(file_path)
            return base64.b64encode(image_bytes).decode("utf-8"), "image/png"
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8"), content_type

    def _parse_response(self, content: str) -> List[DesignStep]:
        data = json.loads(content)
        return [
            DesignStep(
                step_number=step["step_number"],
                instruction=step["instruction"],
            )
            for step in data["steps"]
        ]

    def _build_system_prompt(self) -> str:
        return """あなたは優秀なCADエンジニアです。与えられた2D図面画像を分析し、CadQueryで3Dモデルを作成するための手順を自然言語でステップバイステップに記述してください。

以下のJSON形式で出力してください:
{
  "steps": [
    {"step_number": 1, "instruction": "手順の説明"},
    {"step_number": 2, "instruction": "手順の説明"}
  ]
}

注意事項:
- instruction には具体的な寸法（mm）、形状、位置関係を含めること
- 各ステップは1つのモデリング操作に対応させること
- step_number は 1 から始まる連番"""

    def analyze(self, blueprint: Blueprint) -> List[DesignStep]:
        image_data, mime_type = self._encode_image(blueprint.file_path, blueprint.content_type)
        content = self._call_api(image_data, mime_type)
        return self._parse_response(content)

    @abstractmethod
    def _call_api(self, image_data: str, mime_type: str) -> str:
        """LLM API を呼び出し、JSON 文字列を返す"""
        pass
        
