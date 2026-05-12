"""Step 4-5: 4 視点レンダリング + VLM verifier 1 回分。

CADModel の STL/STEP を 4 視点画像にレンダしてから、元 2D 図面と比較して
不一致を返す。Phase 2 のループ単発分に相当する。
"""
from __future__ import annotations

import os

from loguru import logger

from app.domain.entities.cad_model import CADModel, GenerationStatus
from app.domain.interfaces.blueprint_repository import IBlueprintRepository
from app.domain.interfaces.cad_model_repository import ICADModelRepository
from app.domain.interfaces.line_drawing_four_view_renderer import (
    ILineDrawingFourViewRenderer,
)
from app.domain.interfaces.model_verifier import IModelVerifier
from app.domain.interfaces.shaded_four_view_renderer import IShadedFourViewRenderer
from app.domain.value_objects.verify_outcome import VerifyOutcome


class VerifyCadModelUseCase:
    """1 回分の verify を実行する usecase。

    output_dir には ExecuteScriptUseCase が書き出した STL / STEP がある前提。
    """

    def __init__(
        self,
        output_dir: str,
        blueprint_repo: IBlueprintRepository,
        cad_model_repo: ICADModelRepository,
        line_renderer: ILineDrawingFourViewRenderer,
        shaded_renderer: IShadedFourViewRenderer,
        verifier: IModelVerifier,
    ) -> None:
        self._output_dir = output_dir
        self._blueprint_repo = blueprint_repo
        self._cad_model_repo = cad_model_repo
        self._line_renderer = line_renderer
        self._shaded_renderer = shaded_renderer
        self._verifier = verifier

    def execute(self, model_id: str) -> VerifyOutcome:
        cad_model = self._cad_model_repo.get_by_id(model_id)
        self._mark_status(cad_model, GenerationStatus.RENDERING)

        stl_path, step_path = self._resolve_paths(cad_model)
        blueprint = self._blueprint_repo.get_by_id(cad_model.blueprint_id)

        shaded = self._shaded_renderer.render(stl_path)
        # STEP が出ていないケース（古いモデル等）は STL から線画を作れないので shaded で代用
        line = (
            self._line_renderer.render(step_path)
            if step_path is not None
            else shaded
        )

        self._mark_status(cad_model, GenerationStatus.VERIFYING)
        result = self._verifier.verify(blueprint.file_path, line, shaded)
        cad_model.verification_result = result
        self._cad_model_repo.save(cad_model)

        logger.info(
            f"[verify] model_id={model_id} valid={result.is_valid} "
            f"critical={result.critical_count()} "
            f"major={result.major_count()} minor={result.minor_count()}"
        )
        return VerifyOutcome(
            result=result,
            line_views=line,
            shaded_views=shaded,
            blueprint_image_path=blueprint.file_path,
        )

    def _resolve_paths(self, cad_model: CADModel) -> tuple[str, str | None]:
        if not cad_model.stl_path:
            raise ValueError(f"CADModel {cad_model.id} に STL が無いため verify できません")
        stl = os.path.join(self._output_dir, cad_model.stl_path)
        step = os.path.join(self._output_dir, cad_model.step_path) if cad_model.step_path else None
        return stl, step

    def _mark_status(self, cad_model: CADModel, status: GenerationStatus) -> None:
        cad_model.status = status
        self._cad_model_repo.save(cad_model)
