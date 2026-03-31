from app.domain.entities.cad_model import GenerationStatus
from app.domain.entities.design_intent import DesignIntent
from app.domain.interfaces.cad_model_repository import ICADModelRepository
from app.domain.interfaces.script_generator import IScriptGenerator
from app.domain.value_objects.cad_script import CadScript


class GenerateScriptUseCase:
    """
    Step 2: DesignIntent から CadQuery スクリプトを生成する。
    """

    def __init__(
            self,
            cad_model_repo: ICADModelRepository,
            script_generator: IScriptGenerator
    ):
        self.cad_model_repo = cad_model_repo
        self.script_generator = script_generator

    def execute(self, model_id: str, intent: DesignIntent) -> CadScript:
        """
        DesignIntent から CadQuery スクリプトを生成する。

        Args:
            model_id: 処理対象の CADModel ID
            intent: DesignIntent

        Returns:
            生成された CadScript
        """
        # 状態を生成中に更新
        self.cad_model_repo.update_status(model_id, GenerationStatus.GENERATING)

        # VLM によるスクリプト生成
        script = self.script_generator.generate(intent)

        return script