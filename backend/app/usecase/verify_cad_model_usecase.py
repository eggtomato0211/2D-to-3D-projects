"""Phase 2 検証ユースケース。

[render shaded] + [render line] → [verify] のシーケンスをまとめて実行し、
不一致レポートを返す。fix_script ループとの接続は別ユースケース（後続）に切り出す。
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
from app.domain.value_objects.verification import VerificationResult
from app.domain.value_objects.verify_outcome import VerifyOutcome


class VerifyCadModelUseCase:
    """
    生成済みの CADModel に対し、元 Blueprint と 4視点レンダ（線画+影付き）を比較する。
    """

    def __init__(
        self,
        blueprint_repo: IBlueprintRepository,
        cad_model_repo: ICADModelRepository,
        shaded_renderer: IShadedFourViewRenderer,
        line_renderer: ILineDrawingFourViewRenderer,
        verifier: IModelVerifier,
        cad_output_dir: str,
    ) -> None:
        self.blueprint_repo = blueprint_repo
        self.cad_model_repo = cad_model_repo
        self.shaded_renderer = shaded_renderer
        self.line_renderer = line_renderer
        self.verifier = verifier
        self.cad_output_dir = cad_output_dir

    def execute(self, model_id: str) -> VerifyOutcome:
        """検証実行。判定 + 4 視点レンダ画像 + 参照図面パスを VerifyOutcome で返す。

        画像も返すのは Phase 2-δ §10.1 で Corrector に視覚情報を渡すため。
        単発検証用途では `outcome.result` だけ使えば良い。
        """
        cad_model: CADModel = self.cad_model_repo.get_by_id(model_id)

        if cad_model.stl_path is None:
            raise ValueError(f"CADModel {model_id} に stl_path が無いため検証できません")
        if cad_model.step_path is None:
            raise ValueError(
                f"CADModel {model_id} に step_path が無いため線画レンダができません。"
                "executor が STEP を出力しているか確認してください。"
            )

        blueprint = self.blueprint_repo.get_by_id(cad_model.blueprint_id)

        # 絶対パス化（リポジトリは filename だけ持つ）
        stl_abs = os.path.join(self.cad_output_dir, cad_model.stl_path)
        step_abs = os.path.join(self.cad_output_dir, cad_model.step_path)

        cad_model.status = GenerationStatus.RENDERING
        self.cad_model_repo.save(cad_model)

        logger.info(f"[verify {model_id}] rendering shaded views...")
        shaded = self.shaded_renderer.render(stl_abs)
        logger.info(f"[verify {model_id}] rendering line views...")
        line = self.line_renderer.render(step_abs)

        cad_model.status = GenerationStatus.VERIFYING
        self.cad_model_repo.save(cad_model)

        logger.info(f"[verify {model_id}] calling VLM verifier...")
        result = self.verifier.verify(
            blueprint_image_path=blueprint.file_path,
            line_views=line,
            shaded_views=shaded,
        )

        # 結果ステータス更新（ループは未実装なので validity だけ反映）
        cad_model.status = (
            GenerationStatus.SUCCESS if result.is_valid else GenerationStatus.FAILED
        )
        if not result.is_valid:
            cad_model.error_message = (
                f"検証で {result.critical_count()} 件の critical 不一致を検出"
            )
        self.cad_model_repo.save(cad_model)

        logger.info(
            f"[verify {model_id}] done: is_valid={result.is_valid}, "
            f"critical={result.critical_count()}, "
            f"major={result.major_count()}, minor={result.minor_count()}"
        )
        return VerifyOutcome(
            result=result,
            line_views=line,
            shaded_views=shaded,
            blueprint_image_path=blueprint.file_path,
        )
