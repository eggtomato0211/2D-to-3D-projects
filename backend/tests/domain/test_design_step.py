import pytest
from app.domain.value_objects.design_step import DesignStep


class TestDesignStep:
    def test_create(self):
        # Arrange & Act
        step = DesignStep(
            step_number=1,
            instruction="幅50mm、高さ30mmの長方形をスケッチし、厚さ10mmで押し出してベースを作る",
        )

        # Assert
        assert step.step_number == 1
        assert "50mm" in step.instruction

    def test_step_number_must_be_positive(self):
        # Arrange & Act & Assert
        with pytest.raises(ValueError, match="step_number must be a positive integer"):
            DesignStep(
                step_number=0,
                instruction="Extrude",
            )

    def test_is_frozen(self):
        # Arrange
        step = DesignStep(
            step_number=1,
            instruction="Extrude 10mm",
        )

        # Act & Assert
        with pytest.raises(AttributeError):
            step.step_number = 2
