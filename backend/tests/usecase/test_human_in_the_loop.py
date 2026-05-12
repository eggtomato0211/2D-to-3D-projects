"""§11.5 Human-in-the-loop ユースケースのユニットテスト。"""
from __future__ import annotations

from app.domain.entities.cad_model import CADModel, GenerationStatus
from app.domain.value_objects.cad_script import CadScript
from app.domain.value_objects.discrepancy import Discrepancy
from app.domain.value_objects.execution_result import ExecutionResult
from app.domain.value_objects.four_view_image import FourViewImage
from app.domain.value_objects.tool_call_suggestion import ToolCallSuggestion
from app.domain.value_objects.verification import VerificationResult
from app.domain.value_objects.verify_outcome import VerifyOutcome
from app.infrastructure.persistence.in_memory_cad_model_repository import (
    InMemoryCADModelRepository,
)
from app.usecase.apply_tool_calls_usecase import ApplyToolCallsUseCase
from app.usecase.suggest_corrections_usecase import SuggestCorrectionsUseCase


_DUMMY_PNG = b"\x89PNG"
_DUMMY_VIEWS = FourViewImage(top=_DUMMY_PNG, front=_DUMMY_PNG, side=_DUMMY_PNG, iso=_DUMMY_PNG)


# ---- Stubs ------------------------------------------------------------------
class _StubVerifyUC:
    def __init__(self, result: VerificationResult):
        self.result = result

    def execute(self, model_id: str) -> VerifyOutcome:
        return VerifyOutcome(
            result=self.result,
            line_views=_DUMMY_VIEWS,
            shaded_views=_DUMMY_VIEWS,
            blueprint_image_path="/tmp/bp.png",
        )


class _StubCorrector:
    def __init__(self, suggestions: list[ToolCallSuggestion] | None = None):
        self.suggestions = suggestions or []
        self.suggest_calls = 0
        self.apply_calls = 0
        self.last_apply_args = None

    def suggest_tool_calls(self, script, discrepancies, **kwargs):
        self.suggest_calls += 1
        return list(self.suggestions)

    def apply_tool_calls(self, script, tool_calls, dedup_against_existing=False):
        self.apply_calls += 1
        self.last_apply_args = {
            "tool_calls": list(tool_calls),
            "dedup": dedup_against_existing,
        }
        if not tool_calls:
            return script
        added = "\n# applied: " + ", ".join(tc["name"] for tc in tool_calls)
        return CadScript(content=script.content + added)


class _StubExecutor:
    def __init__(self, fail: bool = False):
        self.fail = fail
        self.calls = 0

    def execute(self, script):
        self.calls += 1
        if self.fail:
            raise RuntimeError("execute failed")
        return ExecutionResult(
            stl_filename=f"x_{self.calls}.stl",
            step_filename=f"x_{self.calls}.step",
        )


def _make_model() -> CADModel:
    return CADModel(
        id="m1",
        blueprint_id="bp",
        status=GenerationStatus.SUCCESS,
        stl_path="orig.stl",
        step_path="orig.step",
        cad_script=CadScript(content="result = ..."),
    )


def _disc(severity="critical", feature="hole"):
    return Discrepancy(
        feature_type=feature, severity=severity,
        description="x", expected="a", actual="b",
    )


# ---- SuggestCorrectionsUseCase tests ----------------------------------------
def test_suggest_returns_verification_and_suggestions():
    repo = InMemoryCADModelRepository()
    repo.save(_make_model())
    verify = _StubVerifyUC(
        VerificationResult.failure(
            feedback="x",
            discrepancies=(_disc("critical"), _disc("major")),
        )
    )
    corrector = _StubCorrector(
        suggestions=[
            ToolCallSuggestion(
                tool_name="add_hole", args={"x": 0, "y": 0, "diameter": 4.5},
                related_discrepancy_index=0, rationale="LLM 推奨",
            ),
        ],
    )
    uc = SuggestCorrectionsUseCase(repo, verify, corrector)
    result = uc.execute("m1")

    assert result.verification.is_valid is False
    assert len(result.verification.discrepancies) == 2
    assert len(result.suggestions) == 1
    assert result.suggestions[0].tool_name == "add_hole"
    assert corrector.suggest_calls == 1


def test_suggest_returns_empty_when_no_discrepancies():
    repo = InMemoryCADModelRepository()
    repo.save(_make_model())
    verify = _StubVerifyUC(VerificationResult.success())
    corrector = _StubCorrector()
    uc = SuggestCorrectionsUseCase(repo, verify, corrector)
    result = uc.execute("m1")

    assert result.verification.is_valid is True
    assert result.suggestions == ()
    # 不一致が無いので corrector の suggest_tool_calls は呼ばれない
    assert corrector.suggest_calls == 0


def test_suggest_raises_when_no_cad_script():
    model = _make_model()
    model.cad_script = None
    repo = InMemoryCADModelRepository()
    repo.save(model)
    verify = _StubVerifyUC(VerificationResult.success())
    corrector = _StubCorrector()
    uc = SuggestCorrectionsUseCase(repo, verify, corrector)
    import pytest
    with pytest.raises(ValueError):
        uc.execute("m1")


# ---- ApplyToolCallsUseCase tests --------------------------------------------
def test_apply_executes_and_updates_model():
    repo = InMemoryCADModelRepository()
    repo.save(_make_model())
    corrector = _StubCorrector()
    executor = _StubExecutor()
    uc = ApplyToolCallsUseCase(repo, executor, corrector)
    result = uc.execute("m1", [
        {"name": "add_hole", "input": {"x": 0, "y": 0, "diameter": 4.5}},
        {"name": "add_pcd_holes", "input": {"pcd_radius": 21, "count": 4, "diameter": 2.5}},
    ])

    assert result.status == GenerationStatus.SUCCESS
    assert result.stl_path == "x_1.stl"
    assert result.step_path == "x_1.step"
    assert corrector.apply_calls == 1
    # ユーザー承認済みなので dedup は False
    assert corrector.last_apply_args["dedup"] is False
    assert len(corrector.last_apply_args["tool_calls"]) == 2
    assert executor.calls == 1


def test_apply_no_op_when_empty_tool_calls():
    repo = InMemoryCADModelRepository()
    repo.save(_make_model())
    corrector = _StubCorrector()
    executor = _StubExecutor()
    uc = ApplyToolCallsUseCase(repo, executor, corrector)
    result = uc.execute("m1", [])

    assert corrector.apply_calls == 0
    assert executor.calls == 0
    # 元の状態のまま
    assert result.stl_path == "orig.stl"


def test_apply_handles_execute_failure():
    repo = InMemoryCADModelRepository()
    repo.save(_make_model())
    corrector = _StubCorrector()
    executor = _StubExecutor(fail=True)
    uc = ApplyToolCallsUseCase(repo, executor, corrector)
    result = uc.execute("m1", [
        {"name": "add_hole", "input": {"x": 0, "y": 0, "diameter": 4.5}},
    ])
    assert result.status == GenerationStatus.FAILED
    assert "execute failed" in (result.error_message or "")


def test_apply_raises_when_no_cad_script():
    model = _make_model()
    model.cad_script = None
    repo = InMemoryCADModelRepository()
    repo.save(model)
    corrector = _StubCorrector()
    executor = _StubExecutor()
    uc = ApplyToolCallsUseCase(repo, executor, corrector)
    import pytest
    with pytest.raises(ValueError):
        uc.execute("m1", [{"name": "add_hole", "input": {}}])
