from dataclasses import dataclass, field
from typing import List
from ..value_objects.design_step import DesignStep

@dataclass
class DesignIntent:
    """
    VLMが図面から読み取った設計意図を表すエンティティ。
    モデリング作業手順（DesignStep）のリストを保持し、段階的に構築される。
    """
    blueprint_id: str
    steps: List[DesignStep] = field(default_factory=list)

    def add_step(self, step: DesignStep):
        self.steps.append(step)