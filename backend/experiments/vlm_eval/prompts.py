"""プロンプトテンプレート。実験で比較する複数バリアントを定義。"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PromptTemplate:
    name: str
    system: str
    user_text: str  # 画像はこれと別に添付


# ----------------------------------------------------------------------------
# P1: 自由記述
# ----------------------------------------------------------------------------
P1_FREEFORM = PromptTemplate(
    name="P1_freeform",
    system=(
        "あなたは機械設計と CAD 検証の専門家です。"
        "2 つの 3D モデルのレンダリング画像を比較して、形状の違いを特定してください。"
    ),
    user_text=(
        "1 枚目の画像群は **正解（reference）** モデルです。\n"
        "2 枚目の画像群は **生成（candidate）** モデルです。\n"
        "candidate が reference に対して**欠落している / 異なる / 余計な**特徴を、"
        "重要度順に箇条書きで挙げてください。\n"
        "推測ではなく、画像から実際に読み取れる差分のみを列挙すること。"
    ),
)


# ----------------------------------------------------------------------------
# P2: チェックリスト形式
# ----------------------------------------------------------------------------
P2_CHECKLIST = PromptTemplate(
    name="P2_checklist",
    system=(
        "あなたは機械設計と CAD 検証の専門家です。"
        "以下のチェックリストに沿って、reference と candidate の画像を比較してください。"
    ),
    user_text=(
        "1 枚目の画像群 = reference（正解）\n"
        "2 枚目の画像群 = candidate（生成結果）\n\n"
        "## チェックリスト\n"
        "以下の各項目について、reference と candidate が **一致 / 不一致** のどちらかを判定し、"
        "不一致の場合は具体的な差分を述べてください。\n"
        "- [ ] 外形寸法（外周輪郭の形状とサイズ）\n"
        "- [ ] 穴の数\n"
        "- [ ] 穴の位置と直径\n"
        "- [ ] 段差・凸ボスの有無\n"
        "- [ ] フィレット（角丸）の有無と半径\n"
        "- [ ] 面取り（C）の有無とサイズ\n"
        "- [ ] スロット・長穴の有無\n"
        "- [ ] その他の特徴\n"
    ),
)


# ----------------------------------------------------------------------------
# P3: 構造化 JSON 出力
# ----------------------------------------------------------------------------
P3_STRUCTURED_JSON = PromptTemplate(
    name="P3_structured_json",
    system=(
        "あなたは機械設計と CAD 検証の専門家です。"
        "2 つの 3D モデルの差分を **JSON 形式** で構造化して出力してください。"
    ),
    user_text=(
        "1 枚目の画像群 = reference（正解）\n"
        "2 枚目の画像群 = candidate（生成結果）\n\n"
        "## 出力フォーマット\n"
        "以下の JSON スキーマで出力してください。``` で囲むこと。\n\n"
        "```json\n"
        "{\n"
        '  "discrepancies": [\n'
        "    {\n"
        '      "feature_type": "hole | slot | boss | step | chamfer | fillet | thread | outline | other",\n'
        '      "severity":     "critical | major | minor",\n'
        '      "description":  "candidate の何が reference と違うか日本語で具体的に",\n'
        '      "expected":     "reference でどうなっているか",\n'
        '      "actual":       "candidate でどうなっているか"\n'
        "    }\n"
        "  ]\n"
        "}\n"
        "```\n\n"
        "差分が無い場合は `discrepancies: []` とすること。"
        "推測は避け、画像から確実に読み取れる差分のみ記載すること。"
    ),
)


# ----------------------------------------------------------------------------
# P4: 構造化 JSON + 過検出抑制（汎用厳密版）
#
# 設計方針:
#   - 国際標準（ISO 128 / ISO 129）と日本標準（JIS B 0001）どちらの図面でも機能する
#   - 観察された過検出パターンに対する原則的禁止を行う（特定記法に依存しない）
#   - 不確実時の hallucination を抑える
# ----------------------------------------------------------------------------
P4_STRUCTURED_STRICT = PromptTemplate(
    name="P4_structured_strict",
    system=(
        "You are a CAD verification expert. Compare two engineering models "
        "and output differences as structured JSON. Suppress over-detection strictly: "
        "do not report differences you are not confident about."
    ),
    user_text=(
        "Set 1 = reference (ground truth / original drawing).\n"
        "Set 2 = candidate (generated model).\n\n"
        "Apply ALL of the following rules. They are universal and apply to any "
        "engineering drawing convention (ISO, ANSI, JIS, etc.).\n\n"
        "## Detection rules (strict)\n\n"
        "### A. One physical feature = one entry\n"
        "- One physical shape difference must produce **exactly one entry**, never split it.\n"
        "- Example: a missing slot must NOT be reported as `slot missing` + `central outline differs` + `boss internal shape differs`. Report it ONCE as `slot missing`.\n"
        "- The same feature visible across multiple views is still one entry.\n\n"
        "### B. View differences are not separate findings\n"
        "- 'Hole missing in front view' and 'shadow of hole absent in side view' describe the **same fact**. Merge them.\n"
        "- Mention multiple views inside a single `description` (e.g. 'visible in front and side views').\n\n"
        "### C. Drawing style noise is not a difference\n"
        "- Differences in line style (solid vs dashed, hidden lines, line thickness), hatching, dimension lines, leader lines, centerlines, construction lines are **rendering style**, not shape.\n"
        "- Do not report them. Focus on geometry only.\n\n"
        "### D. Interpret drawing notation correctly\n"
        "Engineering drawings follow standardized notation. Apply these rules before deciding a feature is missing:\n"
        "- `N-<feature>`: a count of N occurrences of the feature (e.g. `4-R6` means 4 R6 features). Determine which feature type by where it appears in the drawing:\n"
        "  - On outer outline / silhouette → likely scallops or notches\n"
        "  - On internal edges → likely fillets or chamfers\n"
        "- Diameter symbol (φ / Ø / Dia) followed by a number = circular feature size.\n"
        "- Thread spec (e.g. `M3`, `M3×P0.5`, `1/4-20 UNC`) = threaded hole or rod.\n"
        "- PCD / BCD = pitch / bolt circle diameter; holes are placed equally spaced on this circle.\n"
        "- Counterbore (`⌴`, ザグリ, `C'BORE`, `SF`) and countersink (`⌵`, サラ, `CSK`) = stepped hole types.\n"
        "- 'All-around' (`全周`, ALL AROUND) = applied to every applicable edge.\n"
        "- 'From back' / 'reverse side' (`裏より`) = operation applied from the back face.\n"
        "- General tolerance, surface finish, datum symbols do not affect 3D shape.\n"
        "- **Do not flag a feature as missing if it is actually present in candidate** — verify visually before reporting.\n\n"
        "### E. Do not output uncertain differences\n"
        "- Only report differences you can **clearly read from the images**.\n"
        "- Do not report 'slightly shifted', 'somewhat different' impressions.\n"
        "- Image resolution limits apply: features below ~0.5 mm are not reliably visible. **However, if the drawing has a textual annotation about such a feature (e.g. 'C0.5 all around') and the candidate clearly does not have it, you may report based on the annotation.**\n"
        "- If you cannot find a confident difference, return `discrepancies: []`. Do not invent differences to fill the output.\n\n"
        "### F. Severity calibration\n"
        "- `critical`: major structural feature missing or fundamentally different shape (missing hole, missing slot, missing boss, missing through-feature, completely different outline).\n"
        "- `major`: dimensional discrepancy that affects function, missing/wrong fillet/chamfer of significant size, missing counterbore/countersink, wrong thread spec.\n"
        "- `minor`: surface treatment differences (e.g. C0.5 chamfer), small cosmetic radii, finish notation.\n"
        "- Use the lowest severity that fits. Do not inflate severity.\n\n"
        "## Output format\n"
        "Output the following JSON, wrapped in ``` fences. The `description` may be in the same language as the drawing annotations (Japanese if the drawing is JIS-style, English otherwise).\n\n"
        "```json\n"
        "{\n"
        '  "discrepancies": [\n'
        "    {\n"
        '      "feature_type": "hole | slot | boss | step | chamfer | fillet | thread | outline | dimension | other",\n'
        '      "severity":     "critical | major | minor",\n'
        '      "description":  "What in candidate differs from reference, with view references inline. Single physical feature per entry.",\n'
        '      "expected":     "What is in reference",\n'
        '      "actual":       "What is in candidate",\n'
        '      "confidence":   "high | medium"\n'
        "    }\n"
        "  ]\n"
        "}\n"
        "```\n"
        "If no confident differences are found: `{\"discrepancies\": []}`."
    ),
)


ALL_PROMPTS: tuple[PromptTemplate, ...] = (
    P1_FREEFORM, P2_CHECKLIST, P3_STRUCTURED_JSON, P4_STRUCTURED_STRICT,
)
