from dataclasses import dataclass

@dataclass
class DesignStep:
    step_number: int
    instruction: str
    target_feature: str
    parameters: dict