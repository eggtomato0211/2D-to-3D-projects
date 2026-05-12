"""生成 3D モデルと参照図面の不一致を表す値オブジェクト。

Phase 2 検証フローの基本単位。1 つの物理的な特徴の差分を 1 つの Discrepancy として表現する。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

SeverityT = Literal["critical", "major", "minor"]
ConfidenceT = Literal["high", "medium"]
FeatureT = Literal[
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
        location_hint:   §10.0 R2 解消用 — 修正対象の位置情報を構造化
                         例: "PCD φ42 上 上下 2 箇所 (0, ±21)", "中央 (0, 0)", "上面 (>Z)"
        dimension_hint:  §10.0 R2 解消用 — 関連する寸法を構造化
                         例: "φ4.5 + 裏 φ8.8 サラ 深 2", "5mm 幅 × 14mm 長", "C0.5"
    """
    feature_type: FeatureT
    severity: SeverityT
    description: str
    expected: str
    actual: str
    confidence: ConfidenceT = "high"
    location_hint: str | None = None
    dimension_hint: str | None = None

    def to_feedback_line(self) -> str:
        """fix_script に渡せる形式の 1 行フィードバック。"""
        loc = f" location={self.location_hint}" if self.location_hint else ""
        dim = f" dimension={self.dimension_hint}" if self.dimension_hint else ""
        return (
            f"[{self.severity}/{self.feature_type}] {self.description} "
            f"（expected: {self.expected}, actual: {self.actual}{loc}{dim}）"
        )
