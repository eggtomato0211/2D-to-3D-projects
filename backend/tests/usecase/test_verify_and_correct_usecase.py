"""VerifyAndCorrectUseCase のループ挙動をモックで検証。

外部 (VLM, レンダラ, executor) は全部 Stub で差し込む。
"""
from __future__ import annotations

import pytest

from app.domain.entities.cad_model import CADModel, GenerationStatus
from app.domain.value_objects.cad_script import CadScript
from app.domain.value_objects.discrepancy import Discrepancy
from app.domain.value_objects.execution_result import ExecutionResult
from app.domain.value_objects.four_view_image import FourViewImage
from app.domain.value_objects.iteration_attempt import IterationAttempt
from app.domain.value_objects.loop_config import LoopConfig
from app.domain.value_objects.verification import VerificationResult
from app.domain.value_objects.verify_outcome import VerifyOutcome
from app.infrastructure.persistence.in_memory_cad_model_repository import (
    InMemoryCADModelRepository,
)
from app.usecase.verify_and_correct_usecase import VerifyAndCorrectUseCase


_DUMMY_PNG = b"\x89PNG\r\n\x1a\n"  # 中身は本物でなくてよい（テスト用）
_DUMMY_VIEWS = FourViewImage(top=_DUMMY_PNG, front=_DUMMY_PNG, side=_DUMMY_PNG, iso=_DUMMY_PNG)
_DUMMY_BP = "/tmp/dummy_blueprint.png"


# ---- Stubs ------------------------------------------------------------------
class StubVerifyUC:
    """事前に用意した結果を順番に VerifyOutcome として返す"""

    def __init__(self, results: list[VerificationResult]) -> None:
        self.results = results
        self.calls = 0

    def execute(self, model_id: str) -> VerifyOutcome:
        r = self.results[self.calls]
        self.calls += 1
        return VerifyOutcome(
            result=r,
            line_views=_DUMMY_VIEWS,
            shaded_views=_DUMMY_VIEWS,
            blueprint_image_path=_DUMMY_BP,
        )


class StubScriptGen:
    """correct_script を呼ばれたら ID 末尾に v++ する。

    画像引数を受け取った場合は記録（テストで検証する）。
    """

    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.calls = 0
        self.received_images: list[dict] = []

    def correct_script(
        self,
        script: CadScript,
        discrepancies,
        blueprint_image_path=None,
        line_views=None,
        shaded_views=None,
        iteration_history=None,
    ):
        self.calls += 1
        self.received_images.append({
            "blueprint_image_path": blueprint_image_path,
            "line_views": line_views,
            "shaded_views": shaded_views,
            "iteration_history": iteration_history,
            "tried_count": len(discrepancies),
        })
        if self.fail:
            raise RuntimeError("LLM error")
        return CadScript(content=f"# corrected v{self.calls}\n{script.content}")

    # 他の IScriptGenerator メソッドは未使用なので無視
    def generate(self, *a, **kw): raise NotImplementedError
    def fix_script(self, *a, **kw): raise NotImplementedError
    def modify_parameters(self, *a, **kw): raise NotImplementedError


class StubExecutor:
    """毎回ユニーク stl/step ファイル名を返す"""

    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.calls = 0

    def execute(self, script):
        self.calls += 1
        if self.fail:
            raise RuntimeError("StdFail_NotDone")
        return ExecutionResult(
            stl_filename=f"x_{self.calls}.stl",
            step_filename=f"x_{self.calls}.step",
        )


# ---- Helpers ----------------------------------------------------------------
def _disc(severity: str = "critical") -> Discrepancy:
    return Discrepancy(
        feature_type="hole", severity=severity,
        description="x", expected="a", actual="b",
    )


def _fail_result(critical: int = 1, major: int = 0) -> VerificationResult:
    discs = tuple([_disc("critical")] * critical + [_disc("major")] * major)
    return VerificationResult(
        is_valid=False, discrepancies=discs, feedback="fb", raw_response="raw",
    )


def _success() -> VerificationResult:
    return VerificationResult.success(raw_response="ok")


def _make_model() -> CADModel:
    return CADModel(
        id="m1",
        blueprint_id="bp1",
        status=GenerationStatus.SUCCESS,
        stl_path="orig.stl",
        step_path="orig.step",
        cad_script=CadScript(content="result = ..."),
    )


# ---- Tests ------------------------------------------------------------------
def test_loop_succeeds_on_first_iteration():
    repo = InMemoryCADModelRepository()
    repo.save(_make_model())
    verify = StubVerifyUC([_success()])
    uc = VerifyAndCorrectUseCase(
        repo, StubScriptGen(), StubExecutor(), verify,  # type: ignore[arg-type]
        LoopConfig(max_iterations=3),
    )
    cad_model, final, outcome, best_iter = uc.execute("m1")
    assert outcome == "success"
    assert final.is_valid is True
    assert cad_model.status == GenerationStatus.SUCCESS
    assert len(cad_model.verification_history) == 1
    assert cad_model.verification_history[0].outcome == "success"
    assert best_iter == 1


def test_loop_succeeds_after_correction():
    repo = InMemoryCADModelRepository()
    repo.save(_make_model())
    verify = StubVerifyUC([_fail_result(critical=2), _success()])
    sg = StubScriptGen()
    ex = StubExecutor()
    uc = VerifyAndCorrectUseCase(repo, sg, ex, verify, LoopConfig(max_iterations=3))  # type: ignore[arg-type]

    _, final, outcome, best_iter = uc.execute("m1")
    assert outcome == "success"
    assert sg.calls == 1   # 1 回修正した
    assert ex.calls == 1
    assert verify.calls == 2
    assert best_iter == 2  # 修正後の iter が success なので best


def test_loop_hits_max_iterations():
    repo = InMemoryCADModelRepository()
    repo.save(_make_model())
    # 3 回連続失敗
    verify = StubVerifyUC([_fail_result(2), _fail_result(2), _fail_result(2)])
    uc = VerifyAndCorrectUseCase(
        repo, StubScriptGen(), StubExecutor(), verify,  # type: ignore[arg-type]
        LoopConfig(max_iterations=3),
    )
    cad_model, _, outcome, _ = uc.execute("m1")
    assert outcome == "max_iterations"
    assert cad_model.status == GenerationStatus.FAILED
    assert len(cad_model.verification_history) == 3
    assert cad_model.verification_history[-1].outcome == "max_iterations"


def test_loop_detects_degradation():
    repo = InMemoryCADModelRepository()
    repo.save(_make_model())
    # iter1: critical=1, iter2: critical=3 (悪化)
    verify = StubVerifyUC([_fail_result(1), _fail_result(3)])
    uc = VerifyAndCorrectUseCase(
        repo, StubScriptGen(), StubExecutor(), verify,  # type: ignore[arg-type]
        LoopConfig(max_iterations=5, detect_degradation=True),
    )
    cad_model, _, outcome, best_iter = uc.execute("m1")
    assert outcome == "degradation"
    assert cad_model.status == GenerationStatus.FAILED
    # best はより少ない critical の iter1 のはず
    assert best_iter == 1


def test_loop_correct_script_failure():
    repo = InMemoryCADModelRepository()
    repo.save(_make_model())
    verify = StubVerifyUC([_fail_result(1)])
    sg = StubScriptGen(fail=True)
    uc = VerifyAndCorrectUseCase(
        repo, sg, StubExecutor(), verify,  # type: ignore[arg-type]
        LoopConfig(max_iterations=3),
    )
    cad_model, _, outcome, _ = uc.execute("m1")
    assert outcome == "correct_failed"
    assert cad_model.status == GenerationStatus.FAILED


def test_loop_execute_failure():
    repo = InMemoryCADModelRepository()
    repo.save(_make_model())
    verify = StubVerifyUC([_fail_result(1)])
    ex = StubExecutor(fail=True)
    uc = VerifyAndCorrectUseCase(
        repo, StubScriptGen(), ex, verify,  # type: ignore[arg-type]
        LoopConfig(max_iterations=3),
    )
    cad_model, _, outcome, _ = uc.execute("m1")
    assert outcome == "execute_failed"
    assert cad_model.status == GenerationStatus.FAILED


def test_loop_budget_exceeded():
    repo = InMemoryCADModelRepository()
    repo.save(_make_model())
    verify = StubVerifyUC([_fail_result(1), _fail_result(1)])
    cfg = LoopConfig(
        max_iterations=10,
        cost_budget_usd=0.06,            # verify 1 回 (0.05) は通る、2 回目 (0.10) で超過
        cost_per_verify_usd=0.05,
        cost_per_correct_usd=0.02,
    )
    uc = VerifyAndCorrectUseCase(repo, StubScriptGen(), StubExecutor(), verify, cfg)  # type: ignore[arg-type]
    cad_model, _, outcome, _ = uc.execute("m1")
    assert outcome == "budget_exceeded"
    assert cad_model.status == GenerationStatus.FAILED


def test_no_cad_script_raises():
    model = _make_model()
    model.cad_script = None
    repo = InMemoryCADModelRepository()
    repo.save(model)
    verify = StubVerifyUC([])
    uc = VerifyAndCorrectUseCase(repo, StubScriptGen(), StubExecutor(), verify)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        uc.execute("m1")


def test_loop_rolls_back_to_best_iteration_on_degradation():
    """iter2 が一番良い場合、iter3 で悪化しても iter2 の状態に rollback される"""
    repo = InMemoryCADModelRepository()
    repo.save(_make_model())
    # iter1=critical 3, iter2=critical 1 (best), iter3=critical 5 (degradation)
    verify = StubVerifyUC([
        _fail_result(critical=3),
        _fail_result(critical=1),
        _fail_result(critical=5),
    ])
    sg = StubScriptGen()
    ex = StubExecutor()
    uc = VerifyAndCorrectUseCase(
        repo, sg, ex, verify,  # type: ignore[arg-type]
        LoopConfig(max_iterations=5, detect_degradation=True),
    )
    cad_model, final, outcome, best_iter = uc.execute("m1")
    assert outcome == "degradation"
    assert best_iter == 2
    # final は best (iter2) の結果
    assert final.critical_count() == 1
    # iter2 verify 時点の cad_model 状態は「iter1 で execute した結果」なので x_1.*
    # （iter2 verify の前の最後の execute は iter1 の修正による）
    assert cad_model.stl_path == "x_1.stl"
    assert cad_model.step_path == "x_1.step"
    # cad_script も iter1 で修正したもの（v1 が含まれる）
    assert "v1" in cad_model.cad_script.content
    # error_message に best info が入っている
    assert "best iter=2" in (cad_model.error_message or "")


def test_loop_passes_images_to_corrector():
    """§10.1: Corrector が画像（blueprint + line + shaded）を受け取ること"""
    repo = InMemoryCADModelRepository()
    repo.save(_make_model())
    verify = StubVerifyUC([_fail_result(critical=2), _success()])
    sg = StubScriptGen()
    uc = VerifyAndCorrectUseCase(
        repo, sg, StubExecutor(), verify,  # type: ignore[arg-type]
        LoopConfig(max_iterations=3),
    )
    uc.execute("m1")

    # iter 1 で 1 回 correct_script が呼ばれる
    assert sg.calls == 1
    received = sg.received_images[0]
    # 画像が渡っていることを確認
    assert received["blueprint_image_path"] == _DUMMY_BP
    assert received["line_views"] is _DUMMY_VIEWS
    assert received["shaded_views"] is _DUMMY_VIEWS


def test_select_target_discrepancies_single_fix_picks_critical_first():
    """§10.2 R3: single_fix=True なら critical が major より優先される"""
    discs = (
        _disc("major"), _disc("minor"), _disc("critical"), _disc("major"),
    )
    selected = VerifyAndCorrectUseCase._select_target_discrepancies(discs, True)
    assert len(selected) == 1
    assert selected[0].severity == "critical"


def test_select_target_discrepancies_all_when_single_fix_false():
    discs = (_disc("critical"), _disc("major"), _disc("minor"))
    selected = VerifyAndCorrectUseCase._select_target_discrepancies(discs, False)
    assert len(selected) == 3


def test_select_target_discrepancies_returns_empty_when_empty():
    selected = VerifyAndCorrectUseCase._select_target_discrepancies((), True)
    assert selected == ()


def test_select_target_discrepancies_picks_safer_feature_type():
    """同 severity 同 confidence なら、修正容易な hole が boss より優先される"""
    from app.domain.value_objects.discrepancy import Discrepancy
    boss = Discrepancy(
        feature_type="boss", severity="critical",
        description="x", expected="a", actual="b", confidence="high",
    )
    hole = Discrepancy(
        feature_type="hole", severity="critical",
        description="x", expected="a", actual="b", confidence="high",
    )
    selected = VerifyAndCorrectUseCase._select_target_discrepancies((boss, hole), True)
    assert selected[0].feature_type == "hole"


def test_loop_single_fix_mode_passes_only_one_discrepancy():
    """§10.2: ループが Corrector に 1 件だけ渡すこと"""
    repo = InMemoryCADModelRepository()
    repo.save(_make_model())
    # iter1: critical=3, iter2: success
    verify = StubVerifyUC([_fail_result(critical=3, major=2), _success()])
    sg = StubScriptGen()
    uc = VerifyAndCorrectUseCase(
        repo, sg, StubExecutor(), verify,  # type: ignore[arg-type]
        LoopConfig(max_iterations=3, single_fix_per_iteration=True),
    )
    uc.execute("m1")
    # Corrector が呼ばれた時、discrepancies は 1 件のみのはず
    assert sg.calls == 1


def test_loop_all_fix_mode_passes_all_discrepancies():
    repo = InMemoryCADModelRepository()
    repo.save(_make_model())
    verify = StubVerifyUC([_fail_result(critical=3, major=2), _success()])
    sg = StubScriptGen()

    # single_fix_per_iteration=False で全件渡す挙動
    uc = VerifyAndCorrectUseCase(
        repo, sg, StubExecutor(), verify,  # type: ignore[arg-type]
        LoopConfig(max_iterations=3, single_fix_per_iteration=False),
    )
    uc.execute("m1")
    assert sg.calls == 1


def test_loop_passes_iteration_history_to_corrector():
    """§10.3 R5: 2 回目以降の correct_script 呼び出しで iteration_history が渡されること"""
    repo = InMemoryCADModelRepository()
    repo.save(_make_model())
    # 3 回 fail（全て critical=2）してから success
    verify = StubVerifyUC([
        _fail_result(critical=2),
        _fail_result(critical=2),
        _fail_result(critical=2),
        _success(),
    ])
    sg = StubScriptGen()
    uc = VerifyAndCorrectUseCase(
        repo, sg, StubExecutor(), verify,  # type: ignore[arg-type]
        LoopConfig(max_iterations=4, single_fix_per_iteration=False),
    )
    uc.execute("m1")

    # iter 1 の correct_script 呼び出しでは history は None or 空
    first_call = sg.received_images[0]
    assert first_call["iteration_history"] is None or len(first_call["iteration_history"]) == 0
    # iter 2 では iter 1 の試行が 1 件入っている
    second_call = sg.received_images[1]
    assert second_call["iteration_history"] is not None
    assert len(second_call["iteration_history"]) == 1
    assert second_call["iteration_history"][0].iteration == 1
    # iter 3 では 2 件
    third_call = sg.received_images[2]
    assert len(third_call["iteration_history"]) == 2


class StubToolCorrector:
    """tool-based corrector のスタブ — 呼ばれた回数だけカウント"""
    def __init__(self):
        self.calls = 0

    def correct_script(
        self, script, discrepancies,
        blueprint_image_path=None, line_views=None, shaded_views=None,
        iteration_history=None,
    ):
        self.calls += 1
        return CadScript(content=f"# tool-corrected v{self.calls}\n{script.content}")


def test_loop_uses_tool_corrector_when_enabled():
    """§10.6: use_tool_based_correction=True のとき tool corrector が呼ばれる"""
    repo = InMemoryCADModelRepository()
    repo.save(_make_model())
    verify = StubVerifyUC([_fail_result(critical=2), _success()])
    text_sg = StubScriptGen()
    tool_corrector = StubToolCorrector()
    uc = VerifyAndCorrectUseCase(
        repo, text_sg, StubExecutor(), verify,  # type: ignore[arg-type]
        LoopConfig(max_iterations=3, use_tool_based_correction=True),
        tool_based_corrector=tool_corrector,
    )
    uc.execute("m1")
    # Tool corrector が 1 回呼ばれ、text corrector は呼ばれない
    assert tool_corrector.calls == 1
    assert text_sg.calls == 0


def test_loop_uses_text_corrector_when_disabled():
    """既定（False）では text corrector のみ呼ばれる"""
    repo = InMemoryCADModelRepository()
    repo.save(_make_model())
    verify = StubVerifyUC([_fail_result(critical=2), _success()])
    text_sg = StubScriptGen()
    tool_corrector = StubToolCorrector()
    uc = VerifyAndCorrectUseCase(
        repo, text_sg, StubExecutor(), verify,  # type: ignore[arg-type]
        LoopConfig(max_iterations=3, use_tool_based_correction=False),
        tool_based_corrector=tool_corrector,
    )
    uc.execute("m1")
    assert tool_corrector.calls == 0
    assert text_sg.calls == 1


def test_loop_early_stops_when_no_improvement():
    """§10.6 改善 a: 連続で best が改善しない iter があれば早期停止"""
    repo = InMemoryCADModelRepository()
    repo.save(_make_model())
    # iter1: c=3 (best=3), iter2: c=2 (best=2 改善), iter3: c=2 (改善なし → 早期停止)
    verify = StubVerifyUC([
        _fail_result(critical=3),
        _fail_result(critical=2),
        _fail_result(critical=2),
        _fail_result(critical=2),
    ])
    uc = VerifyAndCorrectUseCase(
        repo, StubScriptGen(), StubExecutor(), verify,  # type: ignore[arg-type]
        LoopConfig(max_iterations=10, early_stop_no_improve_k=1),
    )
    cad_model, _, outcome, best_iter = uc.execute("m1")
    assert outcome == "no_improvement"
    assert best_iter == 2  # critical=2 まで届いた iter
    # 4 iter までは行かない（max_iter=10 でも no_improvement で停止）
    assert len(cad_model.verification_history) == 3


def test_loop_no_early_stop_when_continuously_improving():
    """連続改善時は早期停止しない"""
    repo = InMemoryCADModelRepository()
    repo.save(_make_model())
    # iter1: c=3, iter2: c=2, iter3: c=1, iter4: c=0 (success)
    verify = StubVerifyUC([
        _fail_result(critical=3),
        _fail_result(critical=2),
        _fail_result(critical=1),
        _success(),
    ])
    uc = VerifyAndCorrectUseCase(
        repo, StubScriptGen(), StubExecutor(), verify,  # type: ignore[arg-type]
        LoopConfig(max_iterations=10, early_stop_no_improve_k=1),
    )
    _, _, outcome, _ = uc.execute("m1")
    assert outcome == "success"


def test_loop_falls_back_to_text_when_tool_corrector_missing():
    """use_tool_based_correction=True でも tool_corrector=None なら text にフォールバック"""
    repo = InMemoryCADModelRepository()
    repo.save(_make_model())
    verify = StubVerifyUC([_fail_result(critical=2), _success()])
    text_sg = StubScriptGen()
    uc = VerifyAndCorrectUseCase(
        repo, text_sg, StubExecutor(), verify,  # type: ignore[arg-type]
        LoopConfig(max_iterations=3, use_tool_based_correction=True),
        tool_based_corrector=None,
    )
    uc.execute("m1")
    assert text_sg.calls == 1


def test_iteration_attempt_records_tried_and_result():
    """IterationAttempt が tried + result を保持すること"""
    tried = (_disc("critical"), _disc("major"))
    result = (_disc("major"),)  # critical 1件解消
    attempt = IterationAttempt(
        iteration=1,
        tried_discrepancies=tried,
        result_discrepancies=result,
    )
    assert attempt.iteration == 1
    assert len(attempt.tried_discrepancies) == 2
    assert len(attempt.result_discrepancies) == 1


def test_discrepancy_with_location_dimension_hints():
    """§10.0 R2: location_hint / dimension_hint が to_feedback_line に反映される"""
    from app.domain.value_objects.discrepancy import Discrepancy
    d = Discrepancy(
        feature_type="hole", severity="critical",
        description="missing PCD holes",
        expected="2-φ4.5 PCD φ42",
        actual="none",
        confidence="high",
        location_hint="PCD φ42 上 0° / 180°",
        dimension_hint="φ4.5 + 裏 φ8.8 サラ",
    )
    line = d.to_feedback_line()
    assert "location=PCD φ42" in line
    assert "dimension=φ4.5" in line


def test_loop_keeps_initial_state_when_no_correction_helps():
    """iter1 で大量 critical、iter2 では iter1 と全く同じ件数 → best は iter1（最初に出た方）"""
    repo = InMemoryCADModelRepository()
    repo.save(_make_model())
    verify = StubVerifyUC([_fail_result(critical=2), _fail_result(critical=2), _fail_result(critical=2)])
    uc = VerifyAndCorrectUseCase(
        repo, StubScriptGen(), StubExecutor(), verify,  # type: ignore[arg-type]
        LoopConfig(max_iterations=3),
    )
    cad_model, _, outcome, best_iter = uc.execute("m1")
    assert outcome == "max_iterations"
    # 同値タイの場合、最初の iter を best として残す
    assert best_iter == 1
    # iter1 のスクリプトは元の（書き換え無し）
    assert cad_model.cad_script.content == "result = ..."
    assert cad_model.stl_path == "orig.stl"
