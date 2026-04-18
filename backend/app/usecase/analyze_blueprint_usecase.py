import uuid
from app.domain.entities.design_intent import DesignIntent
from app.domain.entities.cad_model import CADModel, GenerationStatus
from app.domain.interfaces.blueprint_repository import IBlueprintRepository
from app.domain.interfaces.cad_model_repository import ICADModelRepository
from app.domain.interfaces.blueprint_analyzer import IBlueprintAnalyzer


class AnalyzeBlueprintUseCase:
    """
    Step 1: 図面を VLM で解析し、設計手順（DesignIntent）を生成する。
    """

    def __init__(
            self,
            blueprint_repo: IBlueprintRepository,
            cad_model_repo: ICADModelRepository,
            blueprint_analyzer: IBlueprintAnalyzer
    ):
        self.blueprint_repo = blueprint_repo
        self.cad_model_repo = cad_model_repo
        self.blueprint_analyzer = blueprint_analyzer

    def execute(self, model_id: str) -> DesignIntent:
        """
        Blueprint を VLM で解析し、DesignIntent を生成する。

        Args:
            model_id: 処理対象の CADModel ID

        Returns:
            生成された DesignIntent（clarifications 含む）
        """
        # 状態を解析中に更新
        self.cad_model_repo.update_status(model_id, GenerationStatus.ANALYZING)

        # データの取得
        cad_model = self.cad_model_repo.get_by_id(model_id)
        blueprint = self.blueprint_repo.get_by_id(cad_model.blueprint_id)

        # VLM による図面解析（DesignIntent を直接取得）
        design_intent = self.blueprint_analyzer.analyze(blueprint)

        # clarifications を CADModel に保存
        cad_model.clarifications = design_intent.clarifications
        cad_model.clarifications_confirmed = False if design_intent.clarifications else True
        cad_model.design_steps = design_intent.steps
        self.cad_model_repo.update(cad_model)

        return design_intent