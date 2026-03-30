import pytest
from app.domain.value_objects.verification import VerificationResult


class TestVerificationResult:
    def test_success_factory(self):
        # Arrange & Act
        result = VerificationResult.success()

        # Assert
        assert result.is_valid is True
        assert result.feedback is None

    def test_failure_factory(self):
        # Arrange
        feedback = "Hole diameter does not match"

        # Act
        result = VerificationResult.failure(feedback)

        # Assert
        assert result.is_valid is False
        assert result.feedback == feedback

    def test_is_frozen(self):
        # Arrange
        result = VerificationResult.success()

        # Act & Assert
        with pytest.raises(AttributeError):
            result.is_valid = False
