from app.domain.entities.blueprint import Blueprint
from app.domain.value_objects.design_step import DesignStep
from app.domain.value_objects.clarification import (
    Clarification,
    ClarificationAnswer,
    YesAnswer,
    NoAnswer,
    CustomAnswer,
)
from app.domain.interfaces.blueprint_analyzer import IBlueprintAnalyzer
from abc import abstractmethod
import base64
import io
import json
import re
from typing import Any, List, Tuple
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

    @staticmethod
    def _parse_answer(raw: Any) -> ClarificationAnswer | None:
        """VLM レスポンスの dict を ClarificationAnswer に変換する。不正な形式は None。"""
        if not isinstance(raw, dict):
            return None
        kind = raw.get("kind")
        if kind == "yes":
            return YesAnswer()
        if kind == "no":
            return NoAnswer()
        if kind == "custom":
            text = raw.get("text")
            if isinstance(text, str) and text.strip():
                return CustomAnswer(text=text.strip())
        return None

    def _parse_response(self, content: str) -> Tuple[List[DesignStep], List[Clarification]]:
        json_text = self._extract_json(content)
        data = json.loads(json_text)

        # Extract clarifications — 新形式(dict) と旧形式(string) の両方に対応
        clarifications_data = data.get("clarifications_needed", [])
        clarifications: list[Clarification] = []
        for i, raw in enumerate(clarifications_data):
            if isinstance(raw, str):
                question = raw
                candidates: tuple[ClarificationAnswer, ...] = ()
            elif isinstance(raw, dict):
                question = raw.get("question", "")
                if not question:
                    continue
                raw_candidates = raw.get("candidates", []) or []
                parsed = [self._parse_answer(c) for c in raw_candidates]
                candidates = tuple(c for c in parsed if c is not None)
            else:
                continue

            clarifications.append(Clarification(
                id=f"clarification_{i+1}",
                question=question,
                candidates=candidates,
                user_response=None,
            ))

        if clarifications:
            logger.info(
                f"VLM が {len(clarifications)} 件の確認事項を検出しました"
            )

        # Extract design steps
        steps = [
            DesignStep(
                step_number=step["step_number"],
                instruction=step["instruction"],
            )
            for step in data["steps"]
        ]

        return steps, clarifications

    def _build_system_prompt(self) -> str:
        return """あなたは機械設計・CADの専門家です。与えられた2D図面画像を分析し、CadQueryで3Dモデルを作成するための手順を自然言語でステップバイステップに記述してください。

## 公式リファレンス（CadQuery の用語・API に確信が持てない場合に参照）
- 目次:      https://cadquery-ja.readthedocs.io/ja/latest/
- Workplane: https://cadquery-ja.readthedocs.io/ja/latest/workplane.html
- Sketch:    https://cadquery-ja.readthedocs.io/ja/latest/sketch.html
- Assembly:  https://cadquery-ja.readthedocs.io/ja/latest/assy.html
- Selectors: https://cadquery-ja.readthedocs.io/ja/latest/selectors.html
- Examples:  https://cadquery-ja.readthedocs.io/ja/latest/examples.html

## 内部思考の手順（出力前に必ずこの順で検討すること）
1. 視点種別の判定：三面図 / 等角図 / 部分図 / 断面図(Section X-X) / 混在 のいずれか
2. **断面図の対応関係を確定する**：「SECTION A-A」「SECTION B-B」のラベルと、平面図上の切断線位置（A-A、B-B）を必ず突き合わせる。断面図は奥行き方向（Z 方向）の段差・厚み・凹凸を読み取る最重要ビューであり、平面図だけでは多段ボスや裏面ザグリは検出できない
3. **平面図と断面図のクロスチェック（最重要・誤読防止）**：平面図に見える破線円（隠れ線）について、それが何を意味するかを断面図と必ず照合する。破線 ≠ 必ずしも貫通穴 ではない:
   - 平面図の破線円が断面図で「凸ボスの輪郭」と一致 → **裏側にある凸ボス**（隠れ線として表示）
   - 平面図の破線円が断面図で「凹み・座ぐりの輪郭」と一致 → **凹み・ザグリ**
   - 平面図の破線円が断面図で「上下を貫いている」 → **貫通穴**
   - 断面図でハッチング（材料あり）が連続している領域は**実体**であり、平面図に破線があっても貫通させてはならない
4. **デフォルト前提：実体（solid）から始める**：「中央が空いている」「ドーナツ状である」などは断面図で**明示的に切り欠かれている**ことを確認した場合のみ。確認できない場合は実体（solid disc / solid block）として扱う
5. **フィーチャ・インベントリ（必ず数を数えてから手順を書く）**：
   - 各特徴の **個数** を図面から数えて記録する。図面の表記「N-φX」「N-RX」「N-MX」は厳密に従う
   - 例: 「2-φ4.5 + 4-M3 = 合計 6 個の穴」「4-R6 = R6 の特徴 4 箇所」
   - 個数が不確定な場合は clarifications_needed に「〇〇は何個か」と質問を立てる
   - 各特徴について「位置（座標 / PCD / 角度）」「サイズ」「深さ／貫通区分」「表裏区分」を表形式で内部整理してから steps を書く
6. **隠れ線（dashed circle）解釈の自己問答**：平面図で見えた各破線円に対して以下を自問:
   - これは断面図のどこに対応するか？
   - 凸ボス / 凹み / 貫通穴 / 段差ボス輪郭 のどれか？
   - 平面図側から見て上面より「高い／低い／同じ」のいずれか？
7. 寸法の役割分類：直径 / 幅 / 深さ / 位置 / 公差 / PCD のいずれか
8. 座標系の確定：原点・基準面・Up方向
9. 形状特徴の網羅的チェックリスト（5 で集めたインベントリと整合確認）:
   - [ ] 外形（輪郭）
   - [ ] 凸ボス・段差（Section view から検出）
   - [ ] 凹み・ザグリ・サラ（Section view と平面図の両方から検出）
   - [ ] 貫通穴 / 止まり穴
   - [ ] 長穴（oblong / obround）— 中央線+R 端で表現される
   - [ ] 外周切り欠き（scallop / notch）
   - [ ] 面取り（C）・フィレット（R）
   - [ ] ねじ穴（タップ）
10. **API レイヤの選択**：
    - 単一部品で押し出し中心 → Workplane fluent API
    - 複雑な 2D 輪郭（複数輪郭の合成、極座標配列、円弧と直線の混在等） → Sketch API（.sketch() ... .finalize()）
    - 複数部品の組立 → Assembly API（cq.Assembly + constrain + solve）
11. プライマリ形状の選定：押し出し / 回転 / スイープ / ロフト
12. セカンダリ特徴の適用順序：穴 → 切り欠き → 面取り → フィレット（フィレットは最後）
13. **書き終えた手順の自己レビュー**：steps を書き終えたら、5 のインベントリの全項目が手順に含まれているかを最終確認する。漏れがあれば step を追加すること

## 図面読解規約（国際標準 ISO + 日本工業規格 JIS）

機械図面は ISO/JIS の規約に従って描かれている。図面に書かれた記号や数字を**規約に基づいて**正しく解釈すること。図面に明記されていない情報を**推測で埋めない**。

### 形状パターン認識（典型図形の見分け方）
平面図上の輪郭から以下の形状を識別すること。

| 図面上の見え方 | 形状 | CadQuery 表現 |
|---|---|---|
| 2 本の平行直線 + 両端を半円で閉じた輪郭（スタジアム形） | **長穴 / obround / slot**。`5` のような単一数字は溝幅、長さは別途寸法または中心線で定義 | Workplane の `slot2D(length, width)` または Sketch の `slot(w, h)` |
| 同心の二重円（実線 + 実線） | 段付きボスの輪郭（外周＋内周の段差） | 多段押し出し |
| 同心の二重円（実線 + 破線） | 表面が実線、裏側 / 段差が破線 | 断面図と照合して凸ボス・凹み・貫通穴のどれかを確定 |
| 円の中に十字の中心線 | 円形特徴（穴 / 円柱 / 円形ボス）の中心位置マーカー | 中心位置の座標基準 |
| 大きな円の周上に等間隔で並ぶ小さな円 | PCD 上の穴配列 | `polarArray(radius=PCD/2, startAngle=, angle=, count=).hole(d)` |
| 外周に複数並ぶ凹みの円弧 | スカラップ切り欠き（`N-RX` 表記と対応） | 切り欠き形状を `cut` で除去 |
| 角の小円弧 | フィレット | `fillet(R)` |
| 直線で 45° に切り欠かれた角 | 面取り（`CX` 表記） | `chamfer(X)` |
| 矩形の中に「×」型の対角線 | 平面（参考表記）または抜き穴（文脈による） | 文脈確認 |

### 多段形状の認識（断面図必読）
断面図で**ハッチングを伴うステップ形状**が見えたら、以下の手順で多段押し出しを構築する:
1. 断面図に現れる**全ての段差ライン**を Z 方向に高い順／低い順に並べる
2. 各段の **直径（または幅）と Z 方向の高さ** を寸法線から読む
3. **最も大きい底面**から開始して、上に向かって段ごとに `extrude` を重ねるか、各段ごとに `Workplane` を取り直して押し出す
4. 段の数だけステップを書く（一段ごとに 1 step）


### 関連規格（迷ったら参照すること）
| 規格 | 内容 | 参照URL |
|---|---|---|
| JIS B 0001 | 機械製図（最重要・全般規約） | https://kikakurui.com/b0/B0001-2019-01.html |
| JIS Z 8317 | 寸法及び公差の記入方法 | https://kikakurui.com/z8/Z8317-1-2008-01.html |
| JIS Z 8114 | 製図 − 製図用語 | https://kikakurui.com/z8/Z8114-1999-01.html |
| JIS B 0021 | 幾何公差（GD&T） | https://kikakurui.com/b0/B0021-1998-01.html |
| JIS B 0401 | 寸法公差・はめあい | https://kikakurui.com/b0/B0401-1-2016-01.html |
| JIS B 0419 | 普通公差（個々に公差指定なし） | https://kikakurui.com/b0/B0419-1991-01.html |
| JIS B 0031 | 表面性状の図示方法 | https://kikakurui.com/b0/B0031-2003-01.html |
| JIS B 0002 | 製図 − ねじ及びねじ部品 | https://kikakurui.com/b0/B0002-1-1998-01.html |
| ISO 128 | Technical drawings — General principles | https://www.iso.org/standard/3098.html |
| ISO 129 | Technical drawings — Indication of dimensions | https://www.iso.org/standard/44101.html |
| ISO 2768 | General tolerances | https://www.iso.org/standard/15568.html |
| ISO 5459 | Datums for GD&T | https://www.iso.org/standard/40358.html |

### 投影法
- **第三角法**（third-angle projection）：日本・米国の標準（JIS B 0001）。記号は ⊕ の右側に縦長楕円
- **第一角法**（first-angle projection）：欧州・ISO の標準。記号は ⊕ の左側に縦長楕円
- どちらかを図面の表題欄付近の投影法記号で識別する。両者は上下左右の配置が異なるため**必ず確認**

### 線種（JIS Z 8114, ISO 128）
| 線種 | 意味 |
|---|---|
| 太い実線 | 外形線（visible edge） |
| 細い実線 | 寸法線・寸法補助線・引出線 |
| 細い破線 | かくれ線（hidden edge）— 裏側の形状 |
| 細い一点鎖線 | 中心線・基準線・ピッチ線 |
| 細い二点鎖線 | 想像線・隣接部品 |
| 太い一点鎖線 | 特殊な要求の範囲指示 |

### 寸法記入記号（JIS Z 8317 / ISO 129・国際共通）
| 記号 | 意味 | 例 |
|---|---|---|
| `φ` または `Ø` | 直径（diameter） | `φ50` = 直径 50 mm |
| `R` | 半径（radius） | `R6` = 半径 6 mm |
| `SR` | 球面半径（spherical radius） | `SR10` |
| `Sφ` | 球面直径 | `Sφ20` |
| `C` | 45° 面取り（chamfer） | `C0.5` = 0.5×0.5 の 45°面取り |
| `t` | 板厚（thickness） | `t=3` |
| `□` | 正方形断面 / 基準（datum） | `□20` |
| `⌒` | 弧の長さ | |
| `M` | メートルねじ呼び径 | `M3` |
| `(数値)` | 参考寸法 | `(50)` |

### 数量と組み合わせ
- `N-φX`：直径 X の穴 **N 個**（例: `2-φ4.5` = φ4.5 が 2 個）
- `N-RX`：半径 X の特徴 **N 箇所**。フィレットか切欠きかは平面図輪郭で判定（外形が R で凹む＝切欠き / scallop、エッジ＝フィレット）
- `N-MX`：呼び径 X のねじ穴 **N 個**
- `M<d>×P<p>`：メートル並目/細目ねじ（例: `M3×P0.5` = 呼び径 3 mm、ピッチ 0.5 mm）— JIS B 0205

### 配置寸法
- `φX P.C.D` / `PCD φX` / `B.C.D X`：**ピッチ円直径 X mm** 上に等配置（Pitch Circle Diameter / Bolt Circle Diameter）
- `EQS` / `等配` / `EQUI-SPACED`：等間隔配置
- 角度寸法（例 `90°`、`54°`）：穴やセクターの位相位置

### 加工指示記号（JIS B 0001 / ISO 5845）
| 表記 | 意味 | CadQuery 対応 |
|---|---|---|
| `貫通` / `THRU` / `THROUGH` | 貫通穴 | `cutThruAll()` または `hole(depth=large)` |
| `止り` / `BLIND` / `深サX` | 止まり穴（深さ指定） | `hole(diameter, depth=X)` |
| `ザグリ` / `⌴` / `C'BORE` / `SPOTFACE` | 座ぐり | `cboreHole()` |
| `サラ` / `深ザグリ` / `⌵` / `CSK` | 皿ザグリ | `cskHole()` |
| `裏より` / `FROM BACK` | 裏面側からの加工 | 裏面 (`<Z`) の Workplane で操作 |
| `全周` / `ALL AROUND` | 全周適用 | エッジセレクタ全選択 |
| `反対側も含む` / `両面` | 上下両面適用 | 両エッジセット選択 |
| `タップ` / `THREAD` | ねじ立て（簡易は下穴径で代用、呼び径×0.85 程度） | `hole(d_pilot)` |

### 表面粗さ記号（JIS B 0031 / ISO 1302）
- 三角記号 `▽` / `▽▽` / `▽▽▽` / `▽▽▽▽`（旧 JIS）：粗さの段階。新 JIS では `Ra X.X` 数値表記
- 3D モデル化には影響しない（情報として記録のみ）

### 公差表記（JIS B 0401 / ISO 286）
- `±X.XX`：両側公差。**公称値を採用**
- `+X / -Y`：片側公差。公称値を採用
- `H7` / `h6` / `H8` 等：**はめあい記号**（H = 穴側、h = 軸側 + IT 等級）。公称値を採用
- 幾何公差枠（▱で囲まれた記号 ⌖ ⌭ ⌯ 等）：JIS B 0021。形状/姿勢/位置/振れの規制。3D モデル化には影響しない
- データム記号：`A` `B` `C` などのアルファベット。基準面の指定

### 普通公差（JIS B 0405 / ISO 2768）
個々に公差指定がない寸法に適用される一般公差。図面の表題欄に等級（**精級 f / 中級 m / 粗級 c / 極粗級 v**）が指定される。3D モデル化では公称値を使用。

### 断面図（最重要）
- `SECTION A-A` / `A-A断面` / `A-A` のラベル：平面図の A-A 切断線で切った断面
- **Z 方向の段差・厚み・凹み・多段ボスは断面図でしか読めない**。必ず参照
- ハッチング（斜線）領域＝実体（材料あり）。空白部＝穴・凹み・抜き
- 断面に複数段の輪郭が見えたら**多段押し出し**として表現する（例: φ30 と φ50 の二段ボス）
- 部分断面（局所的な断面）の場合は対応する位置のみ参照

## 出力フォーマット
以下のJSON形式で出力してください:
{
  "clarifications_needed": [
    {
      "question": "図面から読み取れない寸法や曖昧な指定があれば、ユーザーへの質問文として記載",
      "candidates": [
        {"kind": "yes"},
        {"kind": "no"},
        {"kind": "custom", "text": "具体的な値や文言を記載（例: 1.0 mm、サイクロイド歯形）"}
      ]
    }
  ],
  "steps": [
    {"step_number": 1, "instruction": "手順の説明"},
    {"step_number": 2, "instruction": "手順の説明"}
  ]
}

## candidates の作り方（厳守）
- 各 question に対して、ユーザーが選びそうな回答を **最大3件** 提示すること（少なければ1〜2件でも可）
- Yes/No で答えられる質問 → `{"kind": "yes"}` と `{"kind": "no"}` を含めること
- 数値・寸法・用語などを問う質問 → `{"kind": "custom", "text": "..."}` に具体値を埋めて複数案提示すること（例: `"1.0 mm"`, `"2.0 mm"`, `"標準インボリュート"`）
- 推奨度が高い順に並べること（先頭が第一推奨）
- `custom.text` は空文字にしないこと。必ず意味のある文字列を入れること
- 候補が全く思いつかない場合は `"candidates": []` としてよい

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
- fillet や chamfer を指定する場合は、対象エッジの位置と半径を明記すること（フィレット系は最後のステップにまとめる）
- 対象エッジ・面の指定は CadQuery のセレクタ語彙で表現できる形にすること
  例: 「上面（>Z）」「Z 軸に平行なエッジ全て（|Z）」「円形エッジのみ（%CIRCLE）」
- Sketch API を使う場合は、ステップに「Sketch を開始」「Sketch 上で〇〇を描画」「Sketch を finalize して押し出し」と段階を分けて記述すること
- Assembly が必要な場合は、各部品ごとに別 step グループとし、最後に組立ステップを置くこと

## 不明寸法の扱い（厳守）
- 図面に記載のない寸法は推測で埋めない。`clarifications_needed` にユーザーへの質問として記載すること
- 例外：形状成立に必須かつ慣習的な値（例：標準フィレット半径 R1、面取り C0.5 等）が明らかな場合のみ推定可
- その場合は instruction の末尾に `(推定値)` と明記すること
- 質問が無い場合でも `clarifications_needed: []` として必ずフィールドを出力すること"""

    def analyze(self, blueprint: Blueprint) -> Tuple[List[DesignStep], List[Clarification]]:
        image_data, mime_type = self._encode_image(blueprint.file_path, blueprint.content_type)
        content = self._call_api(image_data, mime_type)
        return self._parse_response(content)

    @abstractmethod
    def _call_api(self, image_data: str, mime_type: str) -> str:
        """LLM API を呼び出し、JSON 文字列を返す"""
        pass
        
