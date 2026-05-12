"""リクエストごとに VLM model_id を受け取って、関連ユースケースを組み立てるファクトリ。

リポジトリやレンダラのような singleton を保持し、毎回 VLM 系コンポーネントだけ
model_factory.build_* で組み立て直す。これによりリクエストごとにモデル選択が
できる一方、ステートレスな部品はインスタンス共有でメモリ効率を保つ。
"""
from __future__ import annotations

from typing import Optional

from app.domain.interfaces.blueprint_repository import IBlueprintRepository
from app.domain.interfaces.cad_executor import ICADExecutor
from app.domain.interfaces.cad_model_repository import ICADModelRepository
from app.domain.interfaces.line_drawing_four_view_renderer import (
    ILineDrawingFourViewRenderer,
)
from app.domain.interfaces.shaded_four_view_renderer import IShadedFourViewRenderer
from app.domain.value_objects.loop_config import LoopConfig
from app.infrastructure.vlm import model_factory
from app.usecase.analyze_blueprint_usecase import AnalyzeBlueprintUseCase
from app.usecase.confirm_clarifications_usecase import ConfirmClarificationsUseCase
from app.usecase.execute_script_usecase import ExecuteScriptUseCase
from app.usecase.generate_and_execute_script_usecase import (
    GenerateAndExecuteScriptUseCase,
)
from app.usecase.generate_cad_usecase import GenerateCadUseCase
from app.usecase.generate_script_usecase import GenerateScriptUseCase
from app.usecase.update_parameters_usecase import UpdateParametersUseCase
from app.usecase.verify_and_correct_usecase import VerifyAndCorrectUseCase
from app.usecase.verify_cad_model_usecase import VerifyCadModelUseCase


class PipelineFactory:

    def __init__(
        self,
        output_dir: str,
        blueprint_repo: IBlueprintRepository,
        cad_model_repo: ICADModelRepository,
        cad_executor: ICADExecutor,
        line_renderer: ILineDrawingFourViewRenderer,
        shaded_renderer: IShadedFourViewRenderer,
    ) -> None:
        self._output_dir = output_dir
        self._blueprint_repo = blueprint_repo
        self._cad_model_repo = cad_model_repo
        self._cad_executor = cad_executor
        self._line_renderer = line_renderer
        self._shaded_renderer = shaded_renderer

    @staticmethod
    def resolve_model(model_id: Optional[str]) -> str:
        if model_id and model_factory.is_supported(model_id):
            return model_id
        return model_factory.DEFAULT_MODEL

    # --- 生成パイプライン ---
    def build_generate_cad(self, vlm_model_id: Optional[str]) -> GenerateCadUseCase:
        resolved = self.resolve_model(vlm_model_id)
        analyzer = model_factory.build_analyzer(resolved)
        script_generator = model_factory.build_script_generator(resolved)

        analyze_uc = AnalyzeBlueprintUseCase(
            self._blueprint_repo, self._cad_model_repo, analyzer,
        )
        generate_script_uc = GenerateScriptUseCase(
            self._cad_model_repo, script_generator,
        )
        execute_uc = ExecuteScriptUseCase(
            self._cad_model_repo, self._cad_executor,
        )
        gae_uc = GenerateAndExecuteScriptUseCase(
            generate_script_uc, execute_uc, script_generator,
        )
        return GenerateCadUseCase(analyze_uc, gae_uc)

    def build_confirm_clarifications(
        self, vlm_model_id: Optional[str]
    ) -> ConfirmClarificationsUseCase:
        resolved = self.resolve_model(vlm_model_id)
        script_generator = model_factory.build_script_generator(resolved)
        generate_script_uc = GenerateScriptUseCase(
            self._cad_model_repo, script_generator,
        )
        execute_uc = ExecuteScriptUseCase(
            self._cad_model_repo, self._cad_executor,
        )
        gae_uc = GenerateAndExecuteScriptUseCase(
            generate_script_uc, execute_uc, script_generator,
        )
        return ConfirmClarificationsUseCase(self._cad_model_repo, gae_uc)

    def build_update_parameters(
        self, vlm_model_id: Optional[str]
    ) -> UpdateParametersUseCase:
        resolved = self.resolve_model(vlm_model_id)
        script_generator = model_factory.build_script_generator(resolved)
        return UpdateParametersUseCase(
            self._cad_model_repo, self._cad_executor, script_generator,
        )

    # --- 検証ループ ---
    def build_verify_and_correct(
        self, vlm_model_id: Optional[str], config: LoopConfig = LoopConfig(),
    ) -> VerifyAndCorrectUseCase:
        resolved = self.resolve_model(vlm_model_id)
        script_generator = model_factory.build_script_generator(resolved)
        verifier = model_factory.build_verifier(resolved)
        verify_uc = VerifyCadModelUseCase(
            self._output_dir,
            self._blueprint_repo, self._cad_model_repo,
            self._line_renderer, self._shaded_renderer, verifier,
        )
        execute_uc = ExecuteScriptUseCase(
            self._cad_model_repo, self._cad_executor,
        )
        return VerifyAndCorrectUseCase(
            self._cad_model_repo, verify_uc, execute_uc, script_generator, config,
        )
