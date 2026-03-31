from app.domain.entities.design_intent import DesignIntent
from app.domain.value_objects.design_step import DesignStep


class TestDesignIntent:
    def test_create_with_empty_steps(self):
        # Arrange & Act
        intent = DesignIntent(id="di-001", blueprint_id="bp-001")

        # Assert
        assert intent.id == "di-001"
        assert intent.blueprint_id == "bp-001"
        assert intent.steps == []

    def test_add_step(self):
        # Arrange
        intent = DesignIntent(id="di-001", blueprint_id="bp-001")
        step = DesignStep(
            step_number=1,
            instruction="Extrude 10mm",
            target_feature="base",
            parameters={"depth": 10},
        )

        # Act
        intent.add_step(step)

        # Assert
        assert len(intent.steps) == 1
        assert intent.steps[0] == step

    def test_add_multiple_steps(self):
        # Arrange
        intent = DesignIntent(id="di-001", blueprint_id="bp-001")
        step1 = DesignStep(
            step_number=1,
            instruction="Extrude 10mm",
            target_feature="base",
            parameters={"depth": 10},
        )
        step2 = DesignStep(
            step_number=2,
            instruction="Cut hole 5mm diameter",
            target_feature="hole",
            parameters={"diameter": 5},
        )

        # Act
        intent.add_step(step1)
        intent.add_step(step2)

        # Assert
        assert len(intent.steps) == 2
        assert intent.steps[0].step_number == 1
        assert intent.steps[1].step_number == 2
