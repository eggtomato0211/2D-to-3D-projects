"""自然言語の指示で CADModel のスクリプトを書き換えるユースケース。

UI のチャットから 1 メッセージごとに呼ばれる。
失敗時はランタイムエラーを fix_script でリカバリーする (最大 MAX_FIX_ATTEMPTS 回)。
"""
from __future__ import annotations

from loguru import logger

from app.domain.entities.cad_model import CADModel, GenerationStatus
from app.domain.interfaces.cad_executor import ICADExecutor
from app.domain.interfaces.cad_model_repository import ICADModelRepository
from app.domain.interfaces.script_generator import IScriptGenerator

MAX_FIX_ATTEMPTS = 3


class EditCadModelUseCase:

    def __init__(
        self,
        cad_model_repo: ICADModelRepository,
        cad_executor: ICADExecutor,
        script_generator: IScriptGenerator,
    ) -> None:
        self._cad_model_repo = cad_model_repo
        self._cad_executor = cad_executor
        self._script_generator = script_generator

    def execute(self, model_id: str, instruction: str) -> CADModel:
        cad_model = self._cad_model_repo.get_by_id(model_id)
        if cad_model is None:
            raise ValueError(f"CADModel が見つかりません: {model_id}")
        if cad_model.cad_script is None:
            raise ValueError(
                "スクリプトが保存されていません。先にモデルを生成してください。"
            )

        logger.info(f"[edit] model={model_id} instruction={instruction!r}")
        script = self._script_generator.edit_script(cad_model.cad_script, instruction)

        cad_model.status = GenerationStatus.EXECUTING
        self._cad_model_repo.save(cad_model)

        for attempt in range(MAX_FIX_ATTEMPTS + 1):
            try:
                result = self._cad_executor.execute(script)
                cad_model.stl_path = result.stl_filename
                cad_model.step_path = result.step_filename
                cad_model.parameters = result.parameters
                cad_model.cad_script = script
                cad_model.status = GenerationStatus.SUCCESS
                cad_model.error_message = None
                logger.info(f"[edit] success (attempt {attempt + 1})")
                break
            except Exception as e:
                if attempt < MAX_FIX_ATTEMPTS:
                    logger.warning(f"[edit] runtime error (attempt {attempt + 1}): {e}")
                    script = self._script_generator.fix_script(script, str(e))
                else:
                    logger.error(f"[edit] failed after retries: {e}")
                    cad_model.status = GenerationStatus.FAILED
                    cad_model.error_message = str(e)

        self._cad_model_repo.save(cad_model)
        return cad_model
