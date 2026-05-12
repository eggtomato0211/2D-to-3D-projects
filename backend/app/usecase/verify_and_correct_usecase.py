"""Phase 2: Verify→Correct ループ。

各 iter で verify → critical>0 (または silhouette IoU 不足) なら corrector で
修正 → execute → 再 verify。critical 件数で best 状態を追跡し、ループ終了時に
best を結果として残す。

silhouette_check_enabled=True のとき、VLM verifier が is_valid=True と言っても
シルエット IoU が threshold 未満なら「形状が乖離」とみなして合成 critical を
注入してループを継続する (ベンチの match_score 二段判定の UI 版)。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from loguru import logger

from app.domain.entities.cad_model import CADModel, GenerationStatus
from app.domain.interfaces.cad_model_repository import ICADModelRepository
from app.domain.interfaces.script_generator import IScriptGenerator
from app.domain.interfaces.silhouette_iou_calculator import ISilhouetteIouCalculator
from app.domain.value_objects.cad_script import CadScript
from app.domain.value_objects.discrepancy import Discrepancy
from app.domain.value_objects.iteration_attempt import IterationAttempt
from app.domain.value_objects.loop_config import LoopConfig
from app.domain.value_objects.verification import VerificationResult
from app.domain.value_objects.verify_outcome import VerifyOutcome
from app.usecase.execute_script_usecase import ExecuteScriptUseCase
from app.usecase.verify_cad_model_usecase import VerifyCadModelUseCase


@dataclass
class _BestState:
    """ループ中で最良だった生成物のスナップショット。"""
    script: CadScript
    stl_path: str
    step_path: Optional[str]
    result: VerificationResult
    silhouette_iou: float
    iteration: int

    @classmethod
    def from_cad_model(
        cls, cad_model: CADModel, silhouette_iou: float, iteration: int,
    ) -> "_BestState":
        assert cad_model.cad_script is not None
        assert cad_model.stl_path is not None
        assert cad_model.verification_result is not None
        return cls(
            script=cad_model.cad_script,
            stl_path=cad_model.stl_path,
            step_path=cad_model.step_path,
            result=cad_model.verification_result,
            silhouette_iou=silhouette_iou,
            iteration=iteration,
        )


def _is_better(candidate: _BestState, current: _BestState) -> bool:
    """順位付け: critical → major → minor → silhouette IoU (高い方が良い)。

    critical/major/minor は少ないほど良い。silhouette IoU は最後のタイブレーカ。
    """
    if candidate.result.critical_count() != current.result.critical_count():
        return candidate.result.critical_count() < current.result.critical_count()
    if candidate.result.major_count() != current.result.major_count():
        return candidate.result.major_count() < current.result.major_count()
    if candidate.result.minor_count() != current.result.minor_count():
        return candidate.result.minor_count() < current.result.minor_count()
    return candidate.silhouette_iou > current.silhouette_iou


def _select_target(
    discrepancies: tuple[Discrepancy, ...],
    single_fix_per_iter: bool,
) -> tuple[Discrepancy, ...]:
    """corrector に渡す不一致を選ぶ。

    single_fix モードなら critical を 1 件、無ければ major を 1 件選んで返す。
    そうでなければ全件渡す。
    """
    if not single_fix_per_iter:
        return discrepancies
    crit = [d for d in discrepancies if d.severity == "critical"]
    if crit:
        return (crit[0],)
    major = [d for d in discrepancies if d.severity == "major"]
    if major:
        return (major[0],)
    return discrepancies


def _make_silhouette_discrepancy(iou: float, threshold: float) -> Discrepancy:
    return Discrepancy(
        feature_type="outline",
        severity="critical",
        description=(
            f"全体形状が図面の輪郭と乖離しています (silhouette IoU = {iou:.2f}, "
            f"要求 >= {threshold:.2f})。図面の主要視点を再度よく見て、"
            "外形・bbox 比率・主要フィーチャの配置を見直してください。"
        ),
        expected="図面に近い外形シルエット",
        actual=f"silhouette IoU = {iou:.2f}",
        confidence="medium",
    )


class VerifyAndCorrectUseCase:
    """検証 → 修正 → 再検証 をループする usecase。"""

    def __init__(
        self,
        cad_model_repo: ICADModelRepository,
        verify_usecase: VerifyCadModelUseCase,
        execute_usecase: ExecuteScriptUseCase,
        script_generator: IScriptGenerator,
        silhouette_calc: Optional[ISilhouetteIouCalculator] = None,
        config: LoopConfig = LoopConfig(),
    ) -> None:
        self._cad_model_repo = cad_model_repo
        self._verify_usecase = verify_usecase
        self._execute_usecase = execute_usecase
        self._script_generator = script_generator
        self._silhouette_calc = silhouette_calc
        self._config = config

    def execute(self, model_id: str) -> CADModel:
        cad_model = self._cad_model_repo.get_by_id(model_id)
        if cad_model.cad_script is None or cad_model.stl_path is None:
            raise ValueError(
                f"CADModel {model_id} は生成済みでないため verify-correct を実行できません"
            )

        outcome, iou = self._verify_and_augment(model_id)
        cad_model = self._cad_model_repo.get_by_id(model_id)
        best = _BestState.from_cad_model(cad_model, iou, iteration=0)

        if outcome.result.is_valid:
            logger.info(
                f"[verify-correct] valid on first verify (model={model_id}, "
                f"silhouette_iou={iou:.3f})"
            )
            return self._finalize(model_id, best)

        history: list[IterationAttempt] = []
        for iter_idx in range(1, self._config.max_iterations + 1):
            target = _select_target(
                best.result.discrepancies, self._config.single_fix_per_iter
            )
            logger.info(
                f"[verify-correct] iter {iter_idx}: correcting {len(target)} discrepancies"
            )

            self._mark_status(model_id, GenerationStatus.CORRECTING)
            corrected = self._script_generator.correct_script(
                script=best.script,
                discrepancies=target,
                blueprint_image_path=outcome.blueprint_image_path,
                line_views=outcome.line_views,
                shaded_views=outcome.shaded_views,
                iteration_history=tuple(history),
            )

            new_model = self._execute_usecase.execute(model_id, corrected)
            if new_model.status == GenerationStatus.FAILED:
                # 修正版がコンパイル失敗 → このイテレーションは捨てて best 維持
                logger.warning(
                    f"[verify-correct] iter {iter_idx}: corrected script failed to compile "
                    f"({new_model.error_message}). keeping best."
                )
                history.append(IterationAttempt(
                    iteration=iter_idx,
                    tried=target,
                    remaining=best.result.discrepancies,
                ))
                continue

            outcome, iou = self._verify_and_augment(model_id)
            new_model = self._cad_model_repo.get_by_id(model_id)
            new_state = _BestState.from_cad_model(new_model, iou, iteration=iter_idx)

            history.append(IterationAttempt(
                iteration=iter_idx,
                tried=target,
                remaining=outcome.result.discrepancies,
            ))

            if _is_better(new_state, best):
                logger.info(
                    f"[verify-correct] iter {iter_idx}: improved "
                    f"critical {best.result.critical_count()} -> {new_state.result.critical_count()}, "
                    f"silhouette {best.silhouette_iou:.3f} -> {new_state.silhouette_iou:.3f}"
                )
                best = new_state
            elif self._config.stop_on_degradation:
                logger.warning(
                    f"[verify-correct] iter {iter_idx}: degraded, stopping early"
                )
                break

            if best.result.is_valid:
                logger.info(f"[verify-correct] iter {iter_idx}: best is valid, stopping")
                break

        cad_model = self._cad_model_repo.get_by_id(model_id)
        cad_model.iteration_history = history
        self._cad_model_repo.save(cad_model)
        return self._finalize(model_id, best)

    def _verify_and_augment(self, model_id: str) -> tuple[VerifyOutcome, float]:
        """verify を 1 回回し、silhouette check が有効なら結果に critical を注入する。

        Returns:
            (拡張済みの VerifyOutcome, 実測 silhouette IoU)
        """
        outcome = self._verify_usecase.execute(model_id)

        if not (
            self._config.silhouette_check_enabled and self._silhouette_calc is not None
        ):
            return outcome, 1.0  # 検査スキップ時は IoU を 1.0 (=完全一致扱い) で記録

        iou = self._silhouette_calc.compute(
            outcome.blueprint_image_path, outcome.line_views
        )

        if iou >= self._config.silhouette_iou_threshold:
            return outcome, iou

        # IoU 不足 → 合成 critical を注入して outcome を作り直す
        synthetic = _make_silhouette_discrepancy(
            iou, self._config.silhouette_iou_threshold
        )
        augmented = VerificationResult.from_discrepancies(
            outcome.result.discrepancies + (synthetic,)
        )
        logger.warning(
            f"[verify-correct] silhouette IoU {iou:.3f} < "
            f"{self._config.silhouette_iou_threshold:.2f}; injecting synthetic critical"
        )

        # CADModel.verification_result も拡張版に差し替え (UI に反映)
        cad_model = self._cad_model_repo.get_by_id(model_id)
        cad_model.verification_result = augmented
        self._cad_model_repo.save(cad_model)

        return (
            VerifyOutcome(
                result=augmented,
                line_views=outcome.line_views,
                shaded_views=outcome.shaded_views,
                blueprint_image_path=outcome.blueprint_image_path,
            ),
            iou,
        )

    def _finalize(self, model_id: str, best: _BestState) -> CADModel:
        """best state を CADModel に書き戻して返す。"""
        cad_model = self._cad_model_repo.get_by_id(model_id)
        cad_model.cad_script = best.script
        cad_model.stl_path = best.stl_path
        cad_model.step_path = best.step_path
        cad_model.verification_result = best.result
        cad_model.status = GenerationStatus.SUCCESS
        cad_model.error_message = None
        self._cad_model_repo.save(cad_model)
        return cad_model

    def _mark_status(self, model_id: str, status: GenerationStatus) -> None:
        cad_model = self._cad_model_repo.get_by_id(model_id)
        cad_model.status = status
        self._cad_model_repo.save(cad_model)
