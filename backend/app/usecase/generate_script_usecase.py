from app.domain.entities.cad_model import GenerationStatus
from app.domain.entities.design_intent import DesignIntent
from app.domain.interfaces.cad_model_repository import ICADModelRepository
from app.domain.interfaces.vlm_service import IVlmService
from app.domain.value_objects.cad_script import CadScript


class GenerateScriptUseCase:
    """
    Step 2: DesignIntent から CadQuery スクリプトを生成する。
    """

    def __init__(
            self,
            cad_model_repo: ICADModelRepository,
            vlm_service: IVlmService
    ):
        self.cad_model_repo = cad_model_repo
        self.vlm_service = vlm_service

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
        script = self.vlm_service.generate_script(intent)

        return script