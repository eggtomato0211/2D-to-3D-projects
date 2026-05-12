"""verify_and_correct ループの挙動テスト（外部 IO は全てモック）。"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.domain.entities.blueprint import Blueprint
from app.domain.entities.cad_model import CADModel, GenerationStatus
from app.domain.value_objects.cad_script import CadScript
from app.domain.value_objects.discrepancy import Discrepancy
from app.domain.value_objects.four_view_image import FourViewImage
from app.domain.value_objects.loop_config import LoopConfig
from app.domain.value_objects.verification import VerificationResult
from app.domain.value_objects.verify_outcome import VerifyOutcome
from app.usecase.verify_and_correct_usecase import VerifyAndCorrectUseCase


def _views() -> FourViewImage:
    return FourViewImage(top=b"", front=b"", side=b"", iso=b"")


def _outcome(result: VerificationResult) -> VerifyOutcome:
    return VerifyOutcome(
        result=result,
        line_views=_views(),
        shaded_views=_views(),
        blueprint_image_path="/bp.png",
    )


def _make_model(model_id: str = "m1") -> CADModel:
    return CADModel(
        id=model_id, blueprint_id="bp1",
        status=GenerationStatus.SUCCESS,
        stl_path="out.stl", step_path="out.step",
        cad_script=CadScript(content="import cadquery as cq\nresult = cq.Workplane()"),
    )


class _Repo:
    def __init__(self, model: CADModel) -> None:
        self._model = model

    def get_by_id(self, _id: str) -> CADModel:
        return self._model

    def save(self, m: CADModel) -> None:
        self._model = m


def test_early_return_when_first_verify_is_valid():
    model = _make_model()
    repo = _Repo(model)

    verify_uc = MagicMock()
    verify_uc.execute.return_value = _outcome(VerificationResult.success())
    # 検証直後に repo.save しているのを擬似
    def _set_result_on_repo(_):
        model.verification_result = VerificationResult.success()
        return _outcome(VerificationResult.success())
    verify_uc.execute.side_effect = _set_result_on_repo

    execute_uc = MagicMock()
    script_gen = MagicMock()

    uc = VerifyAndCorrectUseCase(
        repo, verify_uc, execute_uc, script_gen,
        config=LoopConfig(max_iterations=3),
    )

    result = uc.execute("m1")

    assert result.status == GenerationStatus.SUCCESS
    script_gen.correct_script.assert_not_called()
    execute_uc.execute.assert_not_called()


def test_corrector_loop_runs_until_valid():
    model = _make_model()
    repo = _Repo(model)

    crit = Discrepancy(
        feature_type="hole", severity="critical",
        description="missing", expected="φ4.5", actual="none",
    )
    iter_results = iter([
        VerificationResult.from_discrepancies((crit,)),  # initial: invalid
        VerificationResult.success(),                    # after correct: valid
    ])

    def verify_side_effect(_):
        r = next(iter_results)
        model.verification_result = r
        return _outcome(r)

    verify_uc = MagicMock()
    verify_uc.execute.side_effect = verify_side_effect

    def execute_side_effect(_id, _script):
        model.cad_script = _script
        model.stl_path = "fixed.stl"
        model.step_path = "fixed.step"
        model.status = GenerationStatus.SUCCESS
        model.error_message = None
        return model

    execute_uc = MagicMock(execute=MagicMock(side_effect=execute_side_effect))

    fixed_script = CadScript(content="import cadquery as cq\nresult = cq.Workplane()")
    script_gen = MagicMock()
    script_gen.correct_script.return_value = fixed_script

    uc = VerifyAndCorrectUseCase(
        repo, verify_uc, execute_uc, script_gen,
        config=LoopConfig(max_iterations=3),
    )

    result = uc.execute("m1")

    assert result.status == GenerationStatus.SUCCESS
    assert result.cad_script is fixed_script
    script_gen.correct_script.assert_called_once()


def test_keeps_best_when_correction_compiles_but_degrades():
    """修正版が compile は通ったが critical が増えた場合、best 状態を維持する。"""
    model = _make_model()
    repo = _Repo(model)

    crit = Discrepancy(
        feature_type="hole", severity="critical",
        description="", expected="", actual="",
    )
    two_crit = (crit, crit)

    initial = VerificationResult.from_discrepancies((crit,))
    worse = VerificationResult.from_discrepancies(two_crit)

    results = iter([initial, worse])

    def verify_side_effect(_):
        r = next(results)
        model.verification_result = r
        return _outcome(r)

    verify_uc = MagicMock(execute=MagicMock(side_effect=verify_side_effect))

    def execute_side_effect(_id, _script):
        model.cad_script = _script
        model.status = GenerationStatus.SUCCESS
        return model

    execute_uc = MagicMock(execute=MagicMock(side_effect=execute_side_effect))
    script_gen = MagicMock()
    script_gen.correct_script.return_value = CadScript(
        content="import cadquery as cq\nresult = cq.Workplane()"
    )

    uc = VerifyAndCorrectUseCase(
        repo, verify_uc, execute_uc, script_gen,
        config=LoopConfig(max_iterations=2, stop_on_degradation=True),
    )

    final = uc.execute("m1")

    # best は initial（critical=1）のまま、worse（critical=2）には置き換わらない
    assert final.verification_result is not None
    assert final.verification_result.critical_count() == 1


def test_silhouette_iou_injects_synthetic_critical_when_below_threshold():
    """verifier が valid と言っても silhouette IoU 不足なら critical を注入してループ継続。"""
    model = _make_model()
    repo = _Repo(model)

    valid_then_valid = iter([
        VerificationResult.success(),  # initial — verifier OK, IoU 低 → 注入
        VerificationResult.success(),  # after correct — verifier OK, IoU 高 → 終了
    ])

    def verify_side_effect(_):
        r = next(valid_then_valid)
        model.verification_result = r
        return _outcome(r)

    verify_uc = MagicMock(execute=MagicMock(side_effect=verify_side_effect))

    def execute_side_effect(_id, _script):
        model.cad_script = _script
        model.stl_path = "fixed.stl"
        model.step_path = "fixed.step"
        model.status = GenerationStatus.SUCCESS
        model.error_message = None
        return model

    execute_uc = MagicMock(execute=MagicMock(side_effect=execute_side_effect))

    fixed_script = CadScript(content="import cadquery as cq\nresult = cq.Workplane()")
    script_gen = MagicMock()
    script_gen.correct_script.return_value = fixed_script

    # IoU 1 回目低、2 回目高
    iou_iter = iter([0.05, 0.8])
    silhouette = MagicMock()
    silhouette.compute = MagicMock(side_effect=lambda *_: next(iou_iter))

    uc = VerifyAndCorrectUseCase(
        repo, verify_uc, execute_uc, script_gen,
        silhouette_calc=silhouette,
        config=LoopConfig(
            max_iterations=3,
            silhouette_check_enabled=True,
            silhouette_iou_threshold=0.15,
        ),
    )

    result = uc.execute("m1")

    assert result.status == GenerationStatus.SUCCESS
    # 初回が IoU 0.05 で合成 critical 注入 → corrector が走る
    script_gen.correct_script.assert_called_once()
    # 注入された critical は outline + medium confidence
    called_with = script_gen.correct_script.call_args.kwargs
    target = called_with["discrepancies"]
    assert any(d.feature_type == "outline" for d in target)


def test_silhouette_check_disabled_keeps_verifier_decision():
    """silhouette_check_enabled=False のとき、verifier の is_valid だけで判定される。"""
    model = _make_model()
    repo = _Repo(model)

    def verify_side_effect(_):
        model.verification_result = VerificationResult.success()
        return _outcome(VerificationResult.success())

    verify_uc = MagicMock(execute=MagicMock(side_effect=verify_side_effect))
    execute_uc = MagicMock()
    script_gen = MagicMock()
    # 仮に IoU が低くても disabled なので無視されるはず
    silhouette = MagicMock()
    silhouette.compute = MagicMock(return_value=0.0)

    uc = VerifyAndCorrectUseCase(
        repo, verify_uc, execute_uc, script_gen,
        silhouette_calc=silhouette,
        config=LoopConfig(silhouette_check_enabled=False),
    )

    uc.execute("m1")

    silhouette.compute.assert_not_called()
    script_gen.correct_script.assert_not_called()


def test_raises_when_no_script_yet():
    cad_model = CADModel(
        id="m1", blueprint_id="bp1",
        status=GenerationStatus.PENDING,
    )
    repo = _Repo(cad_model)
    uc = VerifyAndCorrectUseCase(
        repo, MagicMock(), MagicMock(), MagicMock(),
    )

    with pytest.raises(ValueError):
        uc.execute("m1")
