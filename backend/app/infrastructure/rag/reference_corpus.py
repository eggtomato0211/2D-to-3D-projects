"""DeepCAD train split から Reference Code corpus を構築するモジュール。

各エントリの中身:
- id: DeepCAD object id
- features: extract_features() の出力（Ø/R/C 等）
- pseudo_code: JSON 操作列を CadQuery-like 疑似コードに変換したテキスト
- natural_summary: feature_inventory の name を連結した簡易サマリ
- query_text: embedding 用にハイブリッド形式で整形（bbox + features + diameters）
- bbox: スケール正規化後の bounding box (mm)
"""
from __future__ import annotations

import json
import math
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class ReferenceEntry:
    id: str
    natural_summary: str
    bbox: dict       # {"x", "y", "z"} in mm（正規化後）
    features: dict   # diameters / pcd / fillets / chamfers / cylinders_count 等
    pseudo_code: str
    query_text: str


# ----- DeepCAD JSON → 疑似コード walker -----

_EXTRUDE_OP_LABEL = {
    "NewBodyFeatureOperation": "NewBody",
    "JoinFeatureOperation": "Fuse",
    "CutFeatureOperation": "Cut",
    "IntersectFeatureOperation": "Intersect",
}

_EXTENT_TYPE_LABEL = {
    "OneSideFeatureExtentType": "OneSide",
    "SymmetricFeatureExtentType": "Symmetric",
    "TwoSidesFeatureExtentType": "TwoSides",
}


def _format_transform(t: dict | None) -> str:
    if not t:
        return ""
    o = t.get("origin", {})
    z = t.get("z_axis", {})
    return (
        f"origin=({o.get('x', 0):.2f}, {o.get('y', 0):.2f}, {o.get('z', 0):.2f}), "
        f"normal=({z.get('x', 0):.2f}, {z.get('y', 0):.2f}, {z.get('z', 0):.2f})"
    )


def _format_curve(curve: dict) -> str:
    ct = curve.get("type", "")
    if ct == "Line3D":
        sp = curve.get("start_point", {})
        ep = curve.get("end_point", {})
        return (f"  line({sp.get('x', 0):.2f}, {sp.get('y', 0):.2f}) → "
                f"({ep.get('x', 0):.2f}, {ep.get('y', 0):.2f})")
    if ct == "Circle3D":
        c = curve.get("center_point", {})
        r = curve.get("radius", 0)
        return f"  circle r={r:.2f} at ({c.get('x', 0):.2f}, {c.get('y', 0):.2f})"
    if ct == "Arc3D":
        sp = curve.get("start_point", {})
        ep = curve.get("end_point", {})
        return (f"  arc ({sp.get('x', 0):.2f}, {sp.get('y', 0):.2f}) → "
                f"({ep.get('x', 0):.2f}, {ep.get('y', 0):.2f})")
    return f"  {ct}"


def _format_sketch(sketch: dict, idx: int) -> str:
    transform = sketch.get("transform", {})
    profiles = sketch.get("profiles", {})
    lines = [f"({idx}) Sketch: {_format_transform(transform)}"]
    for pid, profile in profiles.items():
        loops = profile.get("loops", [])
        for loop in loops:
            kind = "outer" if loop.get("is_outer") else "inner"
            curves = loop.get("profile_curves", [])
            lines.append(f"  loop ({kind}, {len(curves)} curves):")
            for cv in curves[:6]:  # 多すぎる場合は先頭 6 件まで
                lines.append("  " + _format_curve(cv))
            if len(curves) > 6:
                lines.append(f"    ... ({len(curves) - 6} more curves)")
    return "\n".join(lines)


def _format_extrude(ext: dict, idx: int) -> str:
    op = _EXTRUDE_OP_LABEL.get(ext.get("operation"), ext.get("operation", "?"))
    et = _EXTENT_TYPE_LABEL.get(ext.get("extent_type"), ext.get("extent_type", "?"))
    e_one = ext.get("extent_one", {}).get("distance", {}).get("value", 0)
    e_two = ext.get("extent_two", {}).get("distance", {}).get("value", 0) if "extent_two" in ext else 0
    return (
        f"({idx}) Extrude: op={op}, extent={et}, "
        f"distance={e_one:.2f}"
        + (f"/{e_two:.2f}" if et == "TwoSides" else "")
    )


def json_to_pseudo_code(data: dict, max_chars: int = 1500) -> str:
    """DeepCAD JSON → CadQuery-like 疑似コード文字列。

    出力フォーマット:
        (0) Sketch: origin=..., normal=...
          loop (outer, 4 curves):
            line ... → ...
            ...
        (1) Extrude: op=NewBody, extent=OneSide, distance=10.00
        ...
    """
    entities = data.get("entities", {})
    sequence = data.get("sequence", [])
    parts: list[str] = []
    for idx, item in enumerate(sequence):
        ent_id = item.get("entity")
        ent_type = item.get("type")
        ent = entities.get(ent_id, {})
        if ent_type == "Sketch":
            parts.append(_format_sketch(ent, idx))
        elif ent_type == "ExtrudeFeature":
            parts.append(_format_extrude(ent, idx))
        else:
            parts.append(f"({idx}) {ent_type}")
    out = "\n".join(parts)
    if len(out) > max_chars:
        out = out[: max_chars - 10] + "\n... (truncated)"
    return out


# ----- features / summary / query -----

def _natural_summary_from_features(features_summary: dict) -> str:
    parts: list[str] = []
    diams = features_summary.get("diameters", []) or []
    pcds = features_summary.get("pcd", []) or []
    fillets = features_summary.get("fillets", []) or []
    chamfers = features_summary.get("chamfers", []) or []
    if diams:
        parts.append(f"{len(diams)} unique diameters")
    if pcds:
        parts.append(f"{len(pcds)} PCD pattern(s)")
    if fillets:
        parts.append("with fillet")
    if chamfers:
        parts.append("with chamfer")
    return ", ".join(parts) if parts else "primitive solid"


def build_query_text(bbox: dict, features_summary: dict, extrude_ops: int) -> str:
    """retrieval 用のハイブリッドクエリ文字列を構築。

    bbox + features + diameters の構造化情報 + Phase 1 風サマリを連結。
    """
    diams = features_summary.get("diameters", []) or []
    pcds = features_summary.get("pcd", []) or []
    fillets = features_summary.get("fillets", []) or []
    chamfers = features_summary.get("chamfers", []) or []
    parts = [
        f"Part: bbox {bbox.get('x', 0):.0f}x{bbox.get('y', 0):.0f}x{bbox.get('z', 0):.0f} mm",
        f"Operations: {extrude_ops} extrudes",
    ]
    if diams:
        parts.append("Diameters: " + ", ".join(f"Ø{d:.1f}" for d in diams))
    if pcds:
        pcd_text = "; ".join(
            f"PCD Ø{p['pcd_diameter']:.1f}x{p['count']}-Ø{p['hole_diameter']:.1f}"
            for p in pcds
        )
        parts.append("Patterns: " + pcd_text)
    if fillets:
        parts.append("Fillets: " + ", ".join(f"R{r:.1f}" for r in fillets))
    if chamfers:
        parts.append("Chamfers: " + ", ".join(f"C{c:.1f}" for c in chamfers))
    parts.append("Summary: " + _natural_summary_from_features(features_summary))
    return "\n".join(parts)


# ----- 1 entry の組み立て -----

def build_reference_entry(
    obj_id: str,
    json_data: dict,
    bbox_mm: dict,
    features_summary: dict,
    extrude_ops: int,
) -> ReferenceEntry:
    pseudo = json_to_pseudo_code(json_data)
    summary = _natural_summary_from_features(features_summary)
    query = build_query_text(bbox_mm, features_summary, extrude_ops)
    return ReferenceEntry(
        id=obj_id,
        natural_summary=summary,
        bbox=bbox_mm,
        features=features_summary,
        pseudo_code=pseudo,
        query_text=query,
    )
