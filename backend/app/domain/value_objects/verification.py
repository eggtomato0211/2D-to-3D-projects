from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class VerificationResult:
    """
    生成された3Dモデルと元の図面の検証結果を表す値オブジェクト。
    検証に失敗した場合、フィードバックをもとに再生成ループを回す判断に使われる。
    """
    is_valid: bool #図面通りならtrue
    feedback: Optional[str] = None #エラーや改善点のフィードバック（あれば）

    @classmethod
    def success(cls):
        return cls(is_valid=True)
    
    @classmethod
    def failure(cls, feedback: str):
        return cls(is_valid=False, feedback=feedback)

