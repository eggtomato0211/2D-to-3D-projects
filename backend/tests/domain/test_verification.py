import pytest

from app.domain.value_objects.discrepancy import Discrepancy
from app.domain.value_objects.verification import VerificationResult


def _disc(severity: str) -> Discrepancy:
    return Discrepancy(
        feature_type="hole",
        severity=severity,  # type: ignore[arg-type]
        description="x",
        expected="x",
        actual="y",
    )


class TestVerificationResult:
    def test_success_factory_is_valid(self):
        result = VerificationResult.success()

        assert result.is_valid is True
        assert result.discrepancies == ()

    def test_from_discrepancies_valid_when_no_critical(self):
        result = VerificationResult.from_discrepancies(
            (_disc("major"), _disc("minor")),
        )

        assert result.is_valid is True
        assert result.major_count() == 1
        assert result.minor_count() == 1
        assert result.critical_count() == 0

    def test_from_discrepancies_invalid_when_critical_present(self):
        result = VerificationResult.from_discrepancies(
            (_disc("critical"), _disc("major")),
        )

        assert result.is_valid is False
        assert result.critical_count() == 1
        assert result.major_count() == 1

    def test_is_frozen(self):
        result = VerificationResult.success()

        with pytest.raises(AttributeError):
            result.is_valid = False  # type: ignore[misc]
