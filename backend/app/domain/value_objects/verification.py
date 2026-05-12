from dataclasses import dataclass, field
from typing import Optional

from .discrepancy import Discrepancy


@dataclass(frozen=True)
class VerificationResult:
    """
    生成された3Dモデルと元の図面の検証結果を表す値オブジェクト。
    検証に失敗した場合、フィードバックをもとに再生成ループを回す判断に使われる。

    Attributes:
        is_valid:      critical な不一致が無く、検証が通った場合 True
        discrepancies: 検出された不一致の一覧
        feedback:      fix_script に渡すための整形済み文字列（後方互換）
        raw_response:  VLM の生レスポンス（デバッグ用）
    """
    is_valid: bool
    discrepancies: tuple[Discrepancy, ...] = field(default_factory=tuple)
    feedback: Optional[str] = None
    raw_response: Optional[str] = None

    @classmethod
    def success(cls, raw_response: Optional[str] = None) -> "VerificationResult":
        return cls(is_valid=True, raw_response=raw_response)

    @classmethod
    def failure(
        cls,
        feedback: Optional[str] = None,
        discrepancies: tuple[Discrepancy, ...] = (),
        raw_response: Optional[str] = None,
    ) -> "VerificationResult":
        """旧 API では feedback だけを取っていたので、第一引数は feedback のまま維持。"""
        return cls(
            is_valid=False,
            discrepancies=discrepancies,
            feedback=feedback,
            raw_response=raw_response,
        )

    def critical_count(self) -> int:
        return sum(1 for d in self.discrepancies if d.severity == "critical")

    def major_count(self) -> int:
        return sum(1 for d in self.discrepancies if d.severity == "major")

    def minor_count(self) -> int:
        return sum(1 for d in self.discrepancies if d.severity == "minor")
