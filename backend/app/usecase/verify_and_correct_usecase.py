"""Phase 2: Verify→Correct ループ。

verify → critical>0 なら corrector で修正 → execute → 再レンダ → 再 verify。
critical 件数で best 状態を追跡し、ループ終了時に best を結果として残す。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from loguru import logger

from app.domain.entities.cad_model import CADModel, GenerationStatus
from app.domain.interfaces.cad_model_repository import ICADModelRepository
from app.domain.interfaces.script_generator import IScriptGenerator
from app.domain.value_objects.cad_script import CadScript
from app.domain.value_objects.discrepancy import Discrepancy
from app.domain.value_objects.iteration_attempt import IterationAttempt
from app.domain.value_objects.loop_config import LoopConfig
from app.domain.value_objects.verification import VerificationResult
from app.usecase.execute_script_usecase import ExecuteScriptUseCase
from app.usecase.verify_cad_model_usecase import VerifyCadModelUseCase


@dataclass
class _BestState:
    """ループ中で最良だった生成物のスナップショット。"""
    script: CadScript
    stl_path: str
    step_path: Optional[str]
    result: VerificationResult
    iteration: int

    @classmethod
    def from_cad_model(cls, cad_model: CADModel, iteration: int) -> "_BestState":
        assert cad_model.cad_script is not None
        assert cad_model.stl_path is not None
        assert cad_model.verification_result is not None
        return cls(
            script=cad_model.cad_script,
            stl_path=cad_model.stl_path,
            step_path=cad_model.step_path,
            result=cad_model.verification_result,
            iteration=iteration,
        )


def _is_better(candidate: VerificationResult, current: VerificationResult) -> bool:
    """critical 件数が少ない方が良い。同値なら major、それでも同値なら minor で順位付け。"""
    if candidate.critical_count() != current.critical_count():
        return candidate.critical_count() < current.critical_count()
    if candidate.major_count() != current.major_count():
        return candidate.major_count() < current.major_count()
    return candidate.minor_count() < current.minor_count()


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
    return discrepancies  # critical も major も無いケースは全件渡す


class VerifyAndCorrectUseCase:
    """検証 → 修正 → 再検証 をループする usecase。"""

    def __init__(
        self,
        cad_model_repo: ICADModelRepository,
        verify_usecase: VerifyCadModelUseCase,
        execute_usecase: ExecuteScriptUseCase,
        script_generator: IScriptGenerator,
        config: LoopConfig = LoopConfig(),
    ) -> None:
        self._cad_model_repo = cad_model_repo
        self._verify_usecase = verify_usecase
        self._execute_usecase = execute_usecase
        self._script_generator = script_generator
        self._config = config

    def execute(self, model_id: str) -> CADModel:
        cad_model = self._cad_model_repo.get_by_id(model_id)
        if cad_model.cad_script is None or cad_model.stl_path is None:
            raise ValueError(
                f"CADModel {model_id} は生成済みでないため verify-correct を実行できません"
            )

        outcome = self._verify_usecase.execute(model_id)
        cad_model = self._cad_model_repo.get_by_id(model_id)
        best = _BestState.from_cad_model(cad_model, iteration=0)

        if outcome.result.is_valid:
            logger.info(f"[verify-correct] valid on first verify (model={model_id})")
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

            outcome = self._verify_usecase.execute(model_id)
            new_model = self._cad_model_repo.get_by_id(model_id)
            new_state = _BestState.from_cad_model(new_model, iteration=iter_idx)

            history.append(IterationAttempt(
                iteration=iter_idx,
                tried=target,
                remaining=outcome.result.discrepancies,
            ))

            if _is_better(new_state.result, best.result):
                logger.info(
                    f"[verify-correct] iter {iter_idx}: improved "
                    f"critical {best.result.critical_count()} -> {new_state.result.critical_count()}"
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
