from dataclasses import dataclass


@dataclass(frozen=True)
class DesignStep:
    """
    3Dモデリングにおける1つの作業手順を表す値オブジェクト。
    例：「幅50mm、高さ30mmの長方形をスケッチし、厚さ10mmで押し出してベースを作る」
    """
    step_number: int
    instruction: str

    def __post_init__(self):
        if self.step_number < 1:
            raise ValueError("step_number must be a positive integer")
