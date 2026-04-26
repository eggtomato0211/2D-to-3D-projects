from abc import ABC, abstractmethod
from ..value_objects.cad_script import CadScript
from ..value_objects.clarification import Clarification
from ..value_objects.design_step import DesignStep
from ..value_objects.model_parameter import ModelParameter


class IScriptGenerator(ABC):
    """
    設計手順と確認事項から CadQuery スクリプトを生成するインターフェース（Step 2）
    """

    @abstractmethod
    def generate(
        self,
        steps: list[DesignStep],
        clarifications: list[Clarification],
    ) -> CadScript:
        """設計手順と確認事項から CadQuery スクリプトを生成する"""
        pass

    @abstractmethod
    def fix_script(self, script: CadScript, feedback: str) -> CadScript:
        """生成されたスクリプトに対してフィードバックを反映し、修正する"""
        pass

    @abstractmethod
    def modify_parameters(
        self,
        script: CadScript,
        old_parameters: list[ModelParameter],
        new_parameters: list[ModelParameter],
    ) -> CadScript:
        """パラメータの変更をスクリプトに反映する"""
        pass
