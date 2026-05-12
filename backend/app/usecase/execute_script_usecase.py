from app.domain.entities.cad_model import CADModel, GenerationStatus
from app.domain.interfaces.cad_model_repository import ICADModelRepository
from app.domain.interfaces.cad_executor import ICADExecutor
from app.domain.value_objects.cad_script import CadScript


class ExecuteScriptUseCase:
    """
    Step 3: CadQuery スクリプトを実行し、3D モデルを生成する。
    実行結果（STL ファイルパス）を CADModel に記録する。
    """

    def __init__(
            self,
            cad_model_repo: ICADModelRepository,
            cad_executor: ICADExecutor
    ):
        self.cad_model_repo = cad_model_repo
        self.cad_executor = cad_executor

    def execute(self, model_id: str, script: CadScript) -> CADModel:
        """
        CadQuery スクリプトを実行し、CADModel を更新する。

        Args:
            model_id: 処理対象の CADModel ID
            script: 実行対象の CadScript

        Returns:
            実行結果で更新された CADModel
        """
        cad_model = self.cad_model_repo.get_by_id(model_id)
        cad_model.status = GenerationStatus.EXECUTING
        self.cad_model_repo.save(cad_model)

        try:
            execution_result = self.cad_executor.execute(script)

            cad_model.stl_path = execution_result.stl_filename
            cad_model.step_path = execution_result.step_filename
            cad_model.parameters = execution_result.parameters
            cad_model.cad_script = script
            cad_model.status = GenerationStatus.SUCCESS
            cad_model.error_message = None

        except Exception as e:
            cad_model.status = GenerationStatus.FAILED
            cad_model.error_message = str(e)

        self.cad_model_repo.save(cad_model)

        return cad_model
