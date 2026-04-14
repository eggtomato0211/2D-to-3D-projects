from app.domain.entities.cad_model import CADModel, GenerationStatus
from app.domain.interfaces.cad_model_repository import ICADModelRepository
from app.domain.interfaces.cad_executor import ICADExecutor
from app.domain.interfaces.script_generator import IScriptGenerator
from app.domain.value_objects.model_parameter import ModelParameter
from loguru import logger

MAX_FIX_ATTEMPTS = 3


class UpdateParametersUseCase:
    """
    パラメータ変更を受けて CadQuery スクリプトを修正・再実行し、
    新しい STL とパラメータを返す。
    """

    def __init__(
        self,
        cad_model_repo: ICADModelRepository,
        cad_executor: ICADExecutor,
        script_generator: IScriptGenerator,
    ):
        self.cad_model_repo = cad_model_repo
        self.cad_executor = cad_executor
        self.script_generator = script_generator

    def execute(
        self, model_id: str, new_parameters: list[ModelParameter]
    ) -> CADModel:
        cad_model = self.cad_model_repo.get_by_id(model_id)
        if cad_model is None:
            raise ValueError(f"CADModel が見つかりません: {model_id}")
        if cad_model.cad_script is None:
            raise ValueError("スクリプトが保存されていません。先にモデルを生成してください。")

        # LLM でスクリプトのパラメータを変更
        logger.info(f"パラメータ変更スクリプト生成を開始 (model_id={model_id})")
        modified_script = self.script_generator.modify_parameters(
            cad_model.cad_script,
            cad_model.parameters,
            new_parameters,
        )

        # 再実行（エラー時はリトライ）
        self.cad_model_repo.update_status(model_id, GenerationStatus.EXECUTING)
        cad_model = self.cad_model_repo.get_by_id(model_id)

        for attempt in range(MAX_FIX_ATTEMPTS + 1):
            try:
                execution_result = self.cad_executor.execute(modified_script)
                cad_model.stl_path = execution_result.stl_filename
                cad_model.parameters = execution_result.parameters
                cad_model.cad_script = modified_script
                cad_model.status = GenerationStatus.SUCCESS
                cad_model.error_message = None
                logger.info("パラメータ変更後のスクリプト実行成功")
                break
            except Exception as e:
                if attempt < MAX_FIX_ATTEMPTS:
                    logger.warning(f"実行失敗 (試行 {attempt + 1}): {e}")
                    modified_script = self.script_generator.fix_script(
                        modified_script, str(e)
                    )
                else:
                    logger.error(f"パラメータ変更スクリプトの実行に失敗: {e}")
                    cad_model.status = GenerationStatus.FAILED
                    cad_model.error_message = str(e)

        self.cad_model_repo.update(cad_model)
        return cad_model
