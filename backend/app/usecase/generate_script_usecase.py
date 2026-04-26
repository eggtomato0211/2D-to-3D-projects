from app.domain.entities.cad_model import GenerationStatus
from app.domain.interfaces.cad_model_repository import ICADModelRepository
from app.domain.interfaces.script_generator import IScriptGenerator
from app.domain.value_objects.cad_script import CadScript


class GenerateScriptUseCase:
    """
    Step 2: CADModel に保存された設計手順と確認事項から CadQuery スクリプトを生成する。
    """

    def __init__(
            self,
            cad_model_repo: ICADModelRepository,
            script_generator: IScriptGenerator
    ):
        self.cad_model_repo = cad_model_repo
        self.script_generator = script_generator

    def execute(self, model_id: str) -> CadScript:
        """
        CADModel から設計手順と確認事項を読み出し、CadQuery スクリプトを生成する。

        Args:
            model_id: 処理対象の CADModel ID

        Returns:
            生成された CadScript
        """
        cad_model = self.cad_model_repo.get_by_id(model_id)
        cad_model.status = GenerationStatus.GENERATING
        self.cad_model_repo.save(cad_model)

        return self.script_generator.generate(
            cad_model.design_steps,
            cad_model.clarifications,
        )
