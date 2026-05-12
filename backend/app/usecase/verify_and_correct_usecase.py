"""Phase 2-δ: 検証 → 修正 → 再実行 → 再検証 のループ。

[verify] → critical あり?
   ├─ No → 終了
   └─ Yes:
        [correct_script] → [execute] → [verify] → ... 上限まで

ループ終了時には **best iteration**（critical 件数が最少の状態）にロールバックする。
これにより degradation や max_iterations 到達でも最良の成果物が残る。
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from loguru import logger

from app.domain.entities.cad_model import CADModel, GenerationStatus
from app.domain.interfaces.cad_executor import ICADExecutor
from app.domain.interfaces.cad_model_repository import ICADModelRepository
from app.domain.interfaces.script_generator import IScriptGenerator
from app.domain.value_objects.cad_script import CadScript
from app.domain.value_objects.discrepancy import Discrepancy
from app.domain.value_objects.iteration_attempt import IterationAttempt
from app.domain.value_objects.loop_config import LoopConfig
from app.domain.value_objects.model_parameter import ModelParameter
from app.domain.value_objects.verification import VerificationResult
from app.domain.value_objects.verification_snapshot import (
    LoopOutcomeT,
    VerificationSnapshot,
)
from app.usecase.verify_cad_model_usecase import VerifyCadModelUseCase


@dataclass
class _IterationState:
    """1 iter 分の完全な状態スナップショット（rollback 用）"""
    iteration: int
    cad_script: CadScript
    stl_path: str | None
    step_path: str | None
    parameters: list[ModelParameter]
    verification_result: VerificationResult


def _is_better(a: _IterationState, b: _IterationState | None) -> bool:
    """a が b より良い結果か。critical → major → minor の順に少ないほど良い。同値なら早い iter を優先（=新しい方を採用しない）"""
    if b is None:
        return True
    a_r, b_r = a.verification_result, b.verification_result
    a_key = (a_r.critical_count(), a_r.major_count(), a_r.minor_count())
    b_key = (b_r.critical_count(), b_r.major_count(), b_r.minor_count())
    if a_key != b_key:
        return a_key < b_key
    return False  # 同値なら最初に出た方を残す


class VerifyAndCorrectUseCase:
    """単発の VerifyCadModelUseCase を上限回数だけ反復するラッパー。

    1 イテレーション = verify + (critical あれば) correct → execute
    """

    def __init__(
        self,
        cad_model_repo: ICADModelRepository,
        script_generator: IScriptGenerator,
        cad_executor: ICADExecutor,
        verify_uc: VerifyCadModelUseCase,
        config: LoopConfig | None = None,
        tool_based_corrector=None,  # §10.6: AnthropicToolBasedCorrector or None
    ) -> None:
        self.cad_model_repo = cad_model_repo
        self.script_generator = script_generator
        self.cad_executor = cad_executor
        self.verify_uc = verify_uc
        self.config = config or LoopConfig()
        self.tool_based_corrector = tool_based_corrector

    # ------------------------------------------------------------------
    def execute(
        self, model_id: str, config: LoopConfig | None = None
    ) -> tuple[CADModel, VerificationResult, LoopOutcomeT, int]:
        """ループ実行のエントリポイント。

        Returns:
            (最終 CADModel, 最終 VerificationResult, ループの結末, best_iteration)
            最終 CADModel は best iteration に rollback された状態。
        """
        cfg = config or self.config
        cad_model = self.cad_model_repo.get_by_id(model_id)
        if cad_model.cad_script is None:
            raise ValueError(f"CADModel {model_id} に cad_script が無いため修正できません")

        last_result: VerificationResult | None = None
        prev_critical: int | None = None
        cumulative_cost = 0.0
        # 各 iter の状態を保持。rollback 用
        iter_states: list[_IterationState] = []
        # §10.3 R5: 過去 iter で何を直そうとして何が残ったかの履歴
        iteration_history: list[IterationAttempt] = []
        # 直前の iter で Corrector に渡した tried_discrepancies を保持
        last_tried: tuple[Discrepancy, ...] = ()
        # §10.6 改善 a: 連続で best が改善しない iter 数
        best_critical_so_far = float("inf")
        no_improve_streak = 0
        outcome: LoopOutcomeT = "max_iterations"

        logger.info(
            f"[loop {model_id}] start: max_iter={cfg.max_iterations}, "
            f"budget={cfg.cost_budget_usd}"
        )

        for i in range(1, cfg.max_iterations + 1):
            # --- verify ---
            cumulative_cost += cfg.cost_per_verify_usd
            if cumulative_cost > cfg.cost_budget_usd:
                logger.warning(
                    f"[loop {model_id}] iter={i} budget exceeded before verify "
                    f"({cumulative_cost:.3f} > {cfg.cost_budget_usd})"
                )
                self._record_snapshot(cad_model, i, last_result, "budget_exceeded")
                outcome = "budget_exceeded"
                break

            try:
                outcome_result = self.verify_uc.execute(model_id)
                last_result = outcome_result.result
                last_line_views = outcome_result.line_views
                last_shaded_views = outcome_result.shaded_views
                last_blueprint_path = outcome_result.blueprint_image_path
            except Exception as e:
                logger.error(f"[loop {model_id}] iter={i} verify exception: {e}")
                self._record_snapshot(cad_model, i, None, "execute_failed")
                outcome = "execute_failed"
                last_result = VerificationResult.failure(feedback=str(e))
                break

            crit = last_result.critical_count()
            logger.info(
                f"[loop {model_id}] iter={i} critical={crit} "
                f"major={last_result.major_count()} minor={last_result.minor_count()}"
            )

            # §10.3 R5: 直前の iter で何を直そうとした → 今回の verify で何が残ったか、
            # を IterationAttempt として記録（次回 Corrector 呼び出し時に参考情報として渡す）
            if i > 1 and last_tried:
                iteration_history.append(IterationAttempt(
                    iteration=i - 1,
                    tried_discrepancies=last_tried,
                    result_discrepancies=last_result.discrepancies,
                ))

            # この iter の状態をスナップショット（後で best として復元する用）
            iter_states.append(_IterationState(
                iteration=i,
                cad_script=cad_model.cad_script,
                stl_path=cad_model.stl_path,
                step_path=cad_model.step_path,
                parameters=list(cad_model.parameters),
                verification_result=last_result,
            ))

            # --- 終了判定: 成功 ---
            if last_result.is_valid:
                self._record_snapshot(cad_model, i, last_result, "success")
                outcome = "success"
                break

            # --- degradation 検知 ---
            if (
                cfg.detect_degradation
                and prev_critical is not None
                and crit > prev_critical
            ):
                logger.warning(
                    f"[loop {model_id}] iter={i} degradation: critical {prev_critical} -> {crit}"
                )
                self._record_snapshot(cad_model, i, last_result, "degradation")
                outcome = "degradation"
                break

            self._record_snapshot(cad_model, i, last_result, "in_progress")
            prev_critical = crit

            # §10.6 改善 a: best_critical が連続 K iter 改善しなければ早期停止
            if crit < best_critical_so_far:
                best_critical_so_far = crit
                no_improve_streak = 0
            else:
                no_improve_streak += 1
                if no_improve_streak >= cfg.early_stop_no_improve_k:
                    logger.warning(
                        f"[loop {model_id}] iter={i} early stop: critical hasn't improved "
                        f"for {no_improve_streak} iter (best so far={best_critical_so_far})"
                    )
                    self._update_last_outcome(cad_model, "no_improvement")
                    outcome = "no_improvement"
                    break

            # --- 上限到達？（次の修正をしないで終わる）---
            if i >= cfg.max_iterations:
                logger.warning(f"[loop {model_id}] max iterations reached")
                self._update_last_outcome(cad_model, "max_iterations")
                outcome = "max_iterations"
                break

            # --- correct_script 呼び出し ---
            cumulative_cost += cfg.cost_per_correct_usd
            if cumulative_cost > cfg.cost_budget_usd:
                logger.warning(
                    f"[loop {model_id}] iter={i} budget exceeded before correct"
                )
                self._update_last_outcome(cad_model, "budget_exceeded")
                outcome = "budget_exceeded"
                break

            # §10.2 R3 解消: single_fix_per_iteration=True の場合、critical を 1 件だけ
            # 渡して連鎖崩壊を回避する。優先順位は (severity, confidence, feature_type 重み)
            target_discs = self._select_target_discrepancies(
                last_result.discrepancies, cfg.single_fix_per_iteration
            )
            mode_label = (
                f"single_fix (1/{len(last_result.discrepancies)})"
                if cfg.single_fix_per_iteration else "all_at_once"
            )
            history_arg = tuple(iteration_history) if iteration_history else None
            # §10.6: Tool Use Corrector を使うか自然言語 Corrector を使うか
            using_tools = (
                cfg.use_tool_based_correction and self.tool_based_corrector is not None
            )
            corrector_label = "tool_based" if using_tools else "text_based"
            try:
                logger.info(
                    f"[loop {model_id}] iter={i} correct_script {mode_label} "
                    f"({corrector_label}, history={len(iteration_history)}) ..."
                )
                if using_tools:
                    corrected_script = self.tool_based_corrector.correct_script(
                        cad_model.cad_script,
                        target_discs,
                        blueprint_image_path=last_blueprint_path,
                        line_views=last_line_views,
                        shaded_views=last_shaded_views,
                        iteration_history=history_arg,
                    )
                else:
                    corrected_script = self.script_generator.correct_script(
                        cad_model.cad_script,
                        target_discs,
                        blueprint_image_path=last_blueprint_path,
                        line_views=last_line_views,
                        shaded_views=last_shaded_views,
                        iteration_history=history_arg,
                    )
                # §10.3 R5: 次の iter の verify 時に「何を直そうとしたか」を記録するため
                last_tried = target_discs
            except Exception as e:
                logger.error(f"[loop {model_id}] iter={i} correct_script failed: {e}")
                self._update_last_outcome(cad_model, "correct_failed")
                outcome = "correct_failed"
                break

            # --- execute（既存の error-fix loop が内部で動く想定）---
            try:
                logger.info(f"[loop {model_id}] iter={i} execute corrected script ...")
                exec_result = self.cad_executor.execute(corrected_script)
                cad_model.cad_script = corrected_script
                cad_model.stl_path = exec_result.stl_filename
                cad_model.step_path = exec_result.step_filename
                cad_model.parameters = exec_result.parameters
                cad_model.error_message = None
                self.cad_model_repo.save(cad_model)
            except Exception as e:
                logger.error(f"[loop {model_id}] iter={i} execute failed: {e}")
                self._update_last_outcome(cad_model, "execute_failed")
                outcome = "execute_failed"
                break

        # --- ループ終了後: best iteration を選出して rollback ---
        best_state, best_iter = self._select_and_apply_best(cad_model, iter_states)

        # ステータスを最終的に確定
        if best_state and best_state.verification_result.is_valid:
            cad_model.status = GenerationStatus.SUCCESS
            cad_model.error_message = None
        else:
            cad_model.status = GenerationStatus.FAILED
            cad_model.error_message = self._error_message_for(outcome, best_state)
        self.cad_model_repo.save(cad_model)

        final_result = (
            best_state.verification_result if best_state else (last_result or VerificationResult.success())
        )
        logger.info(
            f"[loop {model_id}] done: outcome={outcome} "
            f"best_iter={best_iter} final_critical={final_result.critical_count()}"
        )
        return cad_model, final_result, outcome, best_iter

    # ------------------------------------------------------------------
    def _select_and_apply_best(
        self,
        cad_model: CADModel,
        iter_states: list[_IterationState],
    ) -> tuple[_IterationState | None, int]:
        """iter 履歴から best を選び、cad_model を best 状態に書き戻す。

        Returns:
            (選ばれた状態, iteration 番号)。履歴空なら (None, 0)。
        """
        if not iter_states:
            return None, 0
        best: _IterationState | None = None
        for s in iter_states:
            if _is_better(s, best):
                best = s
        assert best is not None
        # rollback: best が最終 iter でない場合は cad_model を書き戻す
        if (cad_model.cad_script != best.cad_script
                or cad_model.stl_path != best.stl_path
                or cad_model.step_path != best.step_path):
            logger.info(
                f"[loop {cad_model.id}] rolling back to best iter={best.iteration} "
                f"(critical={best.verification_result.critical_count()})"
            )
            cad_model.cad_script = best.cad_script
            cad_model.stl_path = best.stl_path
            cad_model.step_path = best.step_path
            cad_model.parameters = list(best.parameters)
        return best, best.iteration

    # ------------------------------------------------------------------
    # §10.2 R3: 段階的修正のための discrepancy 選出
    # ------------------------------------------------------------------
    @staticmethod
    def _select_target_discrepancies(
        discrepancies: tuple,
        single_fix: bool,
    ) -> tuple:
        """single_fix=True の場合、最優先 1 件のみ返す。False なら全件返す。

        優先順位:
            1. severity: critical > major > minor
            2. confidence: high > medium
            3. feature_type の修正容易性（slot/hole は壊しにくい、boss/step は壊しやすい）
        """
        if not single_fix or len(discrepancies) <= 1:
            return discrepancies

        # severity と confidence を数値化して降順ソート
        severity_rank = {"critical": 3, "major": 2, "minor": 1}
        confidence_rank = {"high": 2, "medium": 1}
        # feature_type の修正容易性（高いほど安全に直せる）。slot/hole 系は局所的、
        # boss/step 系は構造変更を伴うため後回し
        feature_priority = {
            "hole": 5, "thread": 5,    # 局所的、追加・削除が独立
            "slot": 4,                  # 同上
            "chamfer": 3, "fillet": 3,  # エッジ操作
            "step": 2, "boss": 2,       # 構造変更
            "outline": 1,               # 全体形状変更
            "dimension": 1,
            "other": 1,
        }

        def _rank(d) -> tuple:
            return (
                severity_rank.get(d.severity, 0),
                confidence_rank.get(d.confidence, 0),
                feature_priority.get(d.feature_type, 0),
            )

        sorted_discs = sorted(discrepancies, key=_rank, reverse=True)
        return (sorted_discs[0],)

    @staticmethod
    def _error_message_for(outcome: LoopOutcomeT, best: _IterationState | None) -> str:
        if best is None:
            return f"検証ループ失敗: {outcome}"
        c = best.verification_result.critical_count()
        m = best.verification_result.major_count()
        n = best.verification_result.minor_count()
        return (
            f"検証ループ {outcome}（best iter={best.iteration}）: "
            f"critical={c} major={m} minor={n} 残存"
        )

    def _record_snapshot(
        self,
        cad_model: CADModel,
        iteration: int,
        result: VerificationResult | None,
        outcome: LoopOutcomeT,
    ) -> None:
        snap = VerificationSnapshot(
            iteration=iteration,
            is_valid=result.is_valid if result else False,
            critical_count=result.critical_count() if result else 0,
            major_count=result.major_count() if result else 0,
            minor_count=result.minor_count() if result else 0,
            timestamp=datetime.now(timezone.utc),
            outcome=outcome,
        )
        cad_model.verification_history.append(snap)
        self.cad_model_repo.save(cad_model)

    def _update_last_outcome(self, cad_model: CADModel, outcome: LoopOutcomeT) -> None:
        if not cad_model.verification_history:
            return
        last = cad_model.verification_history[-1]
        cad_model.verification_history[-1] = VerificationSnapshot(
            iteration=last.iteration,
            is_valid=last.is_valid,
            critical_count=last.critical_count,
            major_count=last.major_count,
            minor_count=last.minor_count,
            timestamp=last.timestamp,
            outcome=outcome,
        )
        self.cad_model_repo.save(cad_model)
