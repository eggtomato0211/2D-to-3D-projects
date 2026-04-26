import pytest
from app.domain.value_objects.cad_script import CadScript


class TestCadScript:
    def test_create(self):
        # Arrange & Act
        script = CadScript(content="result = cq.Workplane('XY').box(10, 10, 10)")

        # Assert
        assert script.content == "result = cq.Workplane('XY').box(10, 10, 10)"

    def test_is_frozen(self):
        # Arrange
        script = CadScript(content="code")

        # Act & Assert
        with pytest.raises(AttributeError):
            script.content = "new code"
