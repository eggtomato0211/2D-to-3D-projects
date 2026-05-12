from __future__ import annotations

from dataclasses import dataclass, field

from .discrepancy import Discrepancy


@dataclass(frozen=True)
class VerificationResult:
    """生成 3D モデルと元図面の検証結果。

    is_valid は「critical な不一致が無いこと」と同義。
    major / minor のみであれば valid とみなす（運用方針）。
    """
    is_valid: bool
    discrepancies: tuple[Discrepancy, ...] = field(default_factory=tuple)

    @classmethod
    def success(cls) -> "VerificationResult":
        return cls(is_valid=True)

    @classmethod
    def from_discrepancies(
        cls, discrepancies: tuple[Discrepancy, ...]
    ) -> "VerificationResult":
        has_critical = any(d.severity == "critical" for d in discrepancies)
        return cls(is_valid=not has_critical, discrepancies=discrepancies)

    def critical_count(self) -> int:
        return sum(1 for d in self.discrepancies if d.severity == "critical")

    def major_count(self) -> int:
        return sum(1 for d in self.discrepancies if d.severity == "major")

    def minor_count(self) -> int:
        return sum(1 for d in self.discrepancies if d.severity == "minor")
