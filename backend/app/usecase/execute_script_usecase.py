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
        # 状態を実行中に更新
        self.cad_model_repo.update_status(model_id, GenerationStatus.EXECUTING)

        cad_model = self.cad_model_repo.get_by_id(model_id)

        try:
            # スクリプト実行
            stl_path = self.cad_executor.execute(script)

            # 成功時は STL ファイルパスを記録してステータスを成功に
            cad_model.stl_path = stl_path
            cad_model.status = GenerationStatus.SUCCESS
            cad_model.error_message = None

        except Exception as e:
            # 実行失敗時はエラーメッセージを記録してステータスを失敗に
            cad_model.status = GenerationStatus.FAILED
            cad_model.error_message = str(e)

        # リポジトリに保存
        self.cad_model_repo.update(cad_model)

        return cad_model
