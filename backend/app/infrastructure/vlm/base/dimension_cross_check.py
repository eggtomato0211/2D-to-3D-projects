"""Phase 1 の構造化抽出結果を自己整合性チェックするモジュール。

初回 analyze の結果（dimensions_table / feature_inventory）を VLM に再度見せて、
- 寸法の値ミス
- 数の数え間違い（4-Ø3 を 3-Ø3 と読む等）
- 複数視点間の整合性
- 抜けているフィーチャ
を訂正させる「self-refinement」パス。

これは OCR を使わず VLM の self-consistency に依存する軽量実装で、
真の OCR ハイブリッド（後段の改善ロードマップ）の前段として動く。
"""
from __future__ import annotations

import json
import re
from typing import Any

CROSS_CHECK_SYSTEM_PROMPT = """あなたは機械製図の検査エンジニアです。
ある CAD アシスタントが図面から抽出した `dimensions_table` と `feature_inventory` を渡します。
あなたの仕事は、図面画像と照合してこの抽出が正しいかを判定し、必要があれば訂正することです。

## 検査項目（優先度順）
1. **数の正確性**: "N-φX" 表記の N（個数）が table に正しく反映されているか
2. **寸法値の精度**: 各 symbol の value が図面の数値と一致しているか（小数点・桁の取り違え禁止）
3. **フィーチャの抜け**: 図面にあるが feature_inventory に無い特徴
4. **多視点間の整合**: 同じ寸法が複数視点に出ていて違う値だった場合の誤り
5. **PCD / 配列**: 円形配列やピッチが正しく feature_inventory に記録されているか

## 出力フォーマット（必ず JSON で返す）
{
  "needs_correction": true/false,
  "corrections": {
    "added_dimensions": [...],         // 抜けていた寸法（symbol/value/unit/type/source_view/applied_to を full set で）
    "fixed_dimensions": [               // 既存だが値が違うもの
      {"symbol": "D_outer", "old_value": 25, "new_value": 50, "reason": "..."}
    ],
    "added_features": [...],            // 抜けていたフィーチャ
    "fixed_features": [                 // 既存だが count や dimensions が違うもの
      {"name": "scallop", "field": "count", "old": 3, "new": 4, "reason": "..."}
    ]
  },
  "summary": "簡潔な検査結果（1-2 文）"
}

訂正なしなら `needs_correction: false` で、`corrections` 配下は空配列にしてください。
"""


def build_cross_check_user_text(dims_table: list[dict], feature_inv: list[dict]) -> str:
    """VLM に渡す user text を構築。"""
    return (
        "## 抽出済み dimensions_table\n"
        + json.dumps(dims_table, ensure_ascii=False, indent=2)
        + "\n\n## 抽出済み feature_inventory\n"
        + json.dumps(feature_inv, ensure_ascii=False, indent=2)
        + "\n\nこれらが図面の内容と一致しているか検査し、JSON で結果を返してください。"
    )


def extract_json(text: str) -> dict[str, Any]:
    """LLM 応答から JSON を抽出。失敗時は空 dict。"""
    fence = re.search(r"```(?:json)?\s*\n(.*?)```", text, re.DOTALL)
    if fence:
        raw = fence.group(1).strip()
    else:
        s = text.find("{")
        e = text.rfind("}")
        raw = text[s:e + 1] if (s != -1 and e != -1 and e > s) else text
    try:
        return json.loads(raw)
    except Exception:
        return {}


def apply_corrections(
    dims_table: list[dict],
    feature_inv: list[dict],
    corrections: dict[str, Any],
) -> tuple[list[dict], list[dict]]:
    """corrections を元の table に適用して、訂正済み table を返す。"""
    new_dims = [dict(d) for d in dims_table]
    new_feats = [dict(f) for f in feature_inv]

    # 値修正
    fixed_dims = corrections.get("fixed_dimensions", []) or []
    by_sym = {d.get("symbol"): d for d in new_dims}
    for fix in fixed_dims:
        if not isinstance(fix, dict):
            continue
        sym = fix.get("symbol")
        if sym in by_sym and "new_value" in fix:
            by_sym[sym]["value"] = fix["new_value"]

    # 寸法追加
    added_dims = corrections.get("added_dimensions", []) or []
    for d in added_dims:
        if isinstance(d, dict) and d.get("symbol"):
            new_dims.append(d)

    # フィーチャの field 単位の修正
    fixed_feats = corrections.get("fixed_features", []) or []
    by_name = {f.get("name"): f for f in new_feats}
    for fix in fixed_feats:
        if not isinstance(fix, dict):
            continue
        name = fix.get("name")
        field = fix.get("field")
        if name in by_name and field and "new" in fix:
            by_name[name][field] = fix["new"]

    # フィーチャ追加
    added_feats = corrections.get("added_features", []) or []
    for f in added_feats:
        if isinstance(f, dict) and f.get("name"):
            new_feats.append(f)

    return new_dims, new_feats
