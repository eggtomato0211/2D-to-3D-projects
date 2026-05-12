from app.domain.value_objects.discrepancy import Discrepancy
from app.domain.value_objects.verification import VerificationResult


def _d(severity: str) -> Discrepancy:
    return Discrepancy(
        feature_type="hole", severity=severity,
        description="x", expected="a", actual="b",
    )


def test_success_factory():
    r = VerificationResult.success(raw_response="ok")
    assert r.is_valid is True
    assert r.discrepancies == ()
    assert r.raw_response == "ok"


def test_failure_factory_keeps_discrepancies():
    discs = (_d("critical"), _d("major"))
    r = VerificationResult.failure(
        feedback="fb", discrepancies=discs, raw_response="raw"
    )
    assert r.is_valid is False
    assert len(r.discrepancies) == 2
    assert r.feedback == "fb"


def test_severity_counts():
    discs = (_d("critical"), _d("critical"), _d("major"), _d("minor"))
    r = VerificationResult.failure(discrepancies=discs)
    assert r.critical_count() == 2
    assert r.major_count() == 1
    assert r.minor_count() == 1


def test_failure_factory_legacy_positional_arg():
    """旧 API: failure('feedback message') の呼び出しが引き続き動くこと"""
    r = VerificationResult.failure("Hole diameter does not match")
    assert r.is_valid is False
    assert r.feedback == "Hole diameter does not match"
    assert r.discrepancies == ()
