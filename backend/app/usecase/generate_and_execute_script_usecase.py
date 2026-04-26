from app.domain.entities.cad_model import CADModel
from app.domain.interfaces.script_generator import IScriptGenerator
from app.usecase.execute_script_usecase import ExecuteScriptUseCase
from app.usecase.generate_script_usecase import GenerateScriptUseCase
from loguru import logger

MAX_FIX_ATTEMPTS = 5


class GenerateAndExecuteScriptUseCase:
    """
    Step 2 & 3: CadQuery スクリプトを生成して実行する。
    実行失敗時はエラーメッセージを LLM にフィードバックし、最大 MAX_FIX_ATTEMPTS 回まで修正リトライする。
    """

    def __init__(
        self,
        generate_script_usecase: GenerateScriptUseCase,
        execute_script_usecase: ExecuteScriptUseCase,
        script_generator: IScriptGenerator,
    ):
        self.generate_script_usecase = generate_script_usecase
        self.execute_script_usecase = execute_script_usecase
        self.script_generator = script_generator

    def execute(self, model_id: str) -> CADModel:
        logger.info("[Step 2] スクリプト生成を開始")
        cad_script = self.generate_script_usecase.execute(model_id)
        logger.info("[Step 2] スクリプト生成完了")

        logger.info("[Step 3] スクリプト実行を開始")
        cad_model = self.execute_script_usecase.execute(model_id, cad_script)

        for attempt in range(MAX_FIX_ATTEMPTS):
            if cad_model.error_message is None:
                logger.info("[Step 3] スクリプト実行成功")
                return cad_model

            logger.warning(
                f"[Step 3] 実行失敗 (試行 {attempt + 1}/{MAX_FIX_ATTEMPTS}): "
                f"{cad_model.error_message}"
            )
            logger.info("[Step 3] エラー修正ループ: スクリプトを修正して再実行")
            cad_script = self.script_generator.fix_script(
                cad_script, cad_model.error_message
            )
            cad_model = self.execute_script_usecase.execute(model_id, cad_script)

        if cad_model.error_message is not None:
            logger.error(
                f"[Step 3] 最大リトライ回数({MAX_FIX_ATTEMPTS})を超過。修正失敗"
            )
        return cad_model
