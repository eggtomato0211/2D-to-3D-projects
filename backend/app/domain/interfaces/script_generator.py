from abc import ABC, abstractmethod
from ..entities.design_intent import DesignIntent
from ..value_objects.cad_script import CadScript


class IScriptGenerator(ABC):
    """
    設計意図から CadQuery スクリプトを生成するインターフェース（Step 2）
    """

    @abstractmethod
    def generate(self, design_intent: DesignIntent) -> CadScript:
        """DesignIntent から CadQuery スクリプトを生成する"""
        pass

    @abstractmethod
    def fix_script(self, script: CadScript, feedback: str) -> CadScript:
        """生成されたスクリプトに対してフィードバックを反映し、修正する"""
        pass
