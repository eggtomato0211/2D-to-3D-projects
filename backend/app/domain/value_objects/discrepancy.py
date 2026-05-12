"""生成 3D モデルと元図面の不一致を表す値オブジェクト。

Phase 2 検証フローの基本単位。1 つの物理的な特徴の差分を 1 件として表現する。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

Severity = Literal["critical", "major", "minor"]
Confidence = Literal["high", "medium", "low"]
FeatureType = Literal[
    "outline", "hole", "slot", "boss", "step",
    "chamfer", "fillet", "thread", "dimension", "other",
]


@dataclass(frozen=True)
class Discrepancy:
    """単一の不一致を表す不変値。

    Attributes:
        feature_type:    差分が属する特徴タイプ
        severity:        重要度（critical: 構造欠落 / major: 機能影響 / minor: 装飾）
        description:     candidate が reference とどう違うかの説明
        expected:        reference でどうなっているか
        actual:          candidate でどうなっているか
        confidence:      検出の確信度
        location_hint:   修正対象の位置を構造化したヒント（例: "PCD φ42 上 上下 2 箇所"）
        dimension_hint:  関連する寸法を構造化したヒント（例: "φ4.5 + 裏 φ8.8 サラ 深 2"）
    """
    feature_type: FeatureType
    severity: Severity
    description: str
    expected: str
    actual: str
    confidence: Confidence = "high"
    location_hint: Optional[str] = None
    dimension_hint: Optional[str] = None
