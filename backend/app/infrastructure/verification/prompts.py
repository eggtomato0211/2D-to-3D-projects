"""Phase 2 検証エンジン用プロンプト（P4 — 過検出抑制版）。

vlm_eval 実験で検証済みのプロンプトをそのまま本番用に転記。
規格非依存（ISO/ANSI/JIS のいずれの図面でも機能）+ 過検出抑制ルール 6 件で構成。
"""
from __future__ import annotations

P4_SYSTEM = (
    "You are a CAD verification expert. Compare two engineering models "
    "and output differences as structured JSON. Suppress over-detection strictly: "
    "do not report differences you are not confident about."
)

P4_USER_TEXT = """\
Set 1 = reference (ground truth / original drawing).
Set 2 = candidate (generated model).

Apply ALL of the following rules. They are universal and apply to any
engineering drawing convention (ISO, ANSI, JIS, etc.).

## Detection rules (strict)

### A. One physical feature = one entry
- One physical shape difference must produce **exactly one entry**, never split it.
- Example: a missing slot must NOT be reported as `slot missing` + `central outline differs` + `boss internal shape differs`. Report it ONCE as `slot missing`.
- The same feature visible across multiple views is still one entry.

### B. View differences are not separate findings
- 'Hole missing in front view' and 'shadow of hole absent in side view' describe the **same fact**. Merge them.
- Mention multiple views inside a single `description` (e.g. 'visible in front and side views').

### C. Drawing style noise is not a difference
- Differences in line style (solid vs dashed, hidden lines, line thickness), hatching, dimension lines, leader lines, centerlines, construction lines are **rendering style**, not shape.
- Do not report them. Focus on geometry only.

### D. Interpret drawing notation correctly
Engineering drawings follow standardized notation. Apply these rules before deciding a feature is missing:
- `N-<feature>`: a count of N occurrences of the feature (e.g. `4-R6` means 4 R6 features). Determine which feature type by where it appears in the drawing:
  - On outer outline / silhouette → likely scallops or notches
  - On internal edges → likely fillets or chamfers
- Diameter symbol (φ / Ø / Dia) followed by a number = circular feature size.
- Thread spec (e.g. `M3`, `M3×P0.5`, `1/4-20 UNC`) = threaded hole or rod.
- PCD / BCD = pitch / bolt circle diameter; holes are placed equally spaced on this circle.
- Counterbore (⌴, ザグリ, C'BORE, SF) and countersink (⌵, サラ, CSK) = stepped hole types.
- 'All-around' (全周, ALL AROUND) = applied to every applicable edge.
- 'From back' / 'reverse side' (裏より) = operation applied from the back face.
- General tolerance, surface finish, datum symbols do not affect 3D shape.
- **Do not flag a feature as missing if it is actually present in candidate** — verify visually before reporting.

### E. Do not output uncertain differences
- Only report differences you can **clearly read from the images**.
- Do not report 'slightly shifted', 'somewhat different' impressions.
- Image resolution limits apply: features below ~0.5 mm are not reliably visible. **However, if the drawing has a textual annotation about such a feature (e.g. 'C0.5 all around') and the candidate clearly does not have it, you may report based on the annotation.**
- If you cannot find a confident difference, return `discrepancies: []`. Do not invent differences to fill the output.

### F. Severity calibration
- `critical`:
  - Major structural feature missing or fundamentally different shape (missing hole, missing slot, missing boss, missing through-feature).
  - **Overall outline / silhouette is clearly wrong** (e.g. reference shows a flat plate but candidate is a tall cylinder).
  - **Body count differs** (reference is one solid, candidate has multiple disjoint pieces, or vice versa).
  - **Major dimension off by ≥10%** of the reference value (overall width / height / depth, or large hole diameter).
  - **Wrong axis / orientation** of a primary feature (e.g. cylinder axis horizontal in reference but vertical in candidate after accounting for view orientation).
- `major`:
  - Dimensional discrepancy 3-10% that affects function.
  - Missing/wrong fillet/chamfer of significant size, missing counterbore/countersink, wrong thread spec.
  - Small features (Ø < 5mm) missing.
- `minor`:
  - Surface treatment differences (e.g. C0.5 chamfer), small cosmetic radii, finish notation.
  - Dimensional discrepancy < 3%.
- **Strictness on shape**: if the candidate's overall proportions look obviously different from the reference (e.g. you would not call them the same part), this is `critical` regardless of whether individual features are matched.
- Use the lowest severity that fits — but **do not under-report scale / aspect / orientation problems**. The downstream system depends on `critical=0` meaning "this is essentially the same part as the reference".

## Output format
Output the following JSON, wrapped in ``` fences. The `description` may be in the same language as the drawing annotations (Japanese if the drawing is JIS-style, English otherwise).

The `location_hint` and `dimension_hint` fields help the downstream Corrector
generate precise CadQuery code. Be concrete and specific:
- `location_hint`: where on the part the difference is. Use coordinates or
  CadQuery selectors when possible. Examples:
  - "PCD φ42 on top face, 0° and 180° positions"
  - "central (0, 0)"
  - "outer perimeter, 4 places at 45°/135°/225°/315°"
  - "back face (<Z), φ8.8 counterbore"
- `dimension_hint`: precise sizes / specs copied from the reference drawing.
  Examples:
  - "φ4.5 through + back φ8.8 counterbore depth 2"
  - "5 mm wide × 14 mm long obround slot"
  - "C0.5 all around (両面)"
  - "M3×P0.5 through"
- If a value is unclear in the reference, use null for that field.

```json
{
  "discrepancies": [
    {
      "feature_type":   "hole | slot | boss | step | chamfer | fillet | thread | outline | dimension | other",
      "severity":       "critical | major | minor",
      "description":    "What in candidate differs from reference, with view references inline. Single physical feature per entry.",
      "expected":       "What is in reference",
      "actual":         "What is in candidate",
      "confidence":     "high | medium",
      "location_hint":  "Concrete position on the part (coordinates or selectors), or null",
      "dimension_hint": "Specific dimensions / specs from reference, or null"
    }
  ]
}
```
If no confident differences are found: `{"discrepancies": []}`.
"""
