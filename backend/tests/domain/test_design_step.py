import pytest
from app.domain.value_objects.design_step import DesignStep


class TestDesignStep:
    def test_create(self):
        # Arrange & Act
        step = DesignStep(
            step_number=1,
            instruction="Extrude 10mm",
            target_feature="base",
            parameters={"depth": 10},
        )

        # Assert
        assert step.step_number == 1
        assert step.instruction == "Extrude 10mm"
        assert step.target_feature == "base"
        assert step.parameters == {"depth": 10}

    def test_step_number_must_be_positive(self):
        # Arrange & Act & Assert
        with pytest.raises(ValueError, match="step_number must be a positive integer"):
            DesignStep(
                step_number=0,
                instruction="Extrude",
                target_feature="base",
                parameters={},
            )

    def test_is_frozen(self):
        # Arrange
        step = DesignStep(
            step_number=1,
            instruction="Extrude 10mm",
            target_feature="base",
            parameters={"depth": 10},
        )

        # Act & Assert
        with pytest.raises(AttributeError):
            step.step_number = 2
