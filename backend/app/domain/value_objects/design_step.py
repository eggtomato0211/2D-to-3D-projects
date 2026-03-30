from dataclasses import dataclass
from typing import Dict, Any

@dataclass(frozen=True)
class DesignStep:
    """
    3Dモデリングにおける1つの作業手順を表す値オブジェクト。
    例：「厚さ10mmで押し出す」「中心に直径5mmの穴を開ける」など。
    """
    step_number: int
    instruction: str
    target_feature: str
    parameters: Dict[str, Any]

    def __post_init__(self):
        #バリデーションロジックをここに追加可能
        if self.step_number < 1:
            raise ValueError("step_number must be a positive integer")

