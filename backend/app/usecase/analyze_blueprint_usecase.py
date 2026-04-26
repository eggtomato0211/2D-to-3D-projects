from app.domain.entities.cad_model import CADModel, GenerationStatus
from app.domain.interfaces.blueprint_repository import IBlueprintRepository
from app.domain.interfaces.cad_model_repository import ICADModelRepository
from app.domain.interfaces.blueprint_analyzer import IBlueprintAnalyzer


class AnalyzeBlueprintUseCase:
    """
    Step 1: 図面を VLM で解析し、設計手順と確認事項を CADModel に記録する。
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

    def execute(self, model_id: str) -> CADModel:
        """
        Blueprint を VLM で解析し、CADModel に steps / clarifications を保存する。

        Args:
            model_id: 処理対象の CADModel ID

        Returns:
            steps / clarifications が反映された CADModel
        """
        cad_model = self.cad_model_repo.get_by_id(model_id)
        cad_model.status = GenerationStatus.ANALYZING
        self.cad_model_repo.save(cad_model)

        blueprint = self.blueprint_repo.get_by_id(cad_model.blueprint_id)
        steps, clarifications = self.blueprint_analyzer.analyze(blueprint)

        cad_model.design_steps = steps
        cad_model.clarifications = clarifications
        cad_model.clarifications_confirmed = not clarifications
        self.cad_model_repo.save(cad_model)

        return cad_model
