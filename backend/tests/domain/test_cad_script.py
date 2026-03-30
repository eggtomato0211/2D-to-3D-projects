import pytest
from app.domain.value_objects.cad_script import CadScript


class TestCadScript:
    def test_create_with_default_language(self):
        # Arrange & Act
        script = CadScript(content="result = cq.Workplane('XY').box(10, 10, 10)")

        # Assert
        assert script.content == "result = cq.Workplane('XY').box(10, 10, 10)"
        assert script.language == "python"

    def test_is_empty_returns_false_for_valid_content(self):
        # Arrange
        script = CadScript(content="result = cq.Workplane('XY').box(10, 10, 10)")

        # Act & Assert
        assert script.is_empty() is False

    def test_is_empty_returns_true_for_blank_content(self):
        # Arrange
        script = CadScript(content="   ")

        # Act & Assert
        assert script.is_empty() is True

    def test_is_frozen(self):
        # Arrange
        script = CadScript(content="code")

        # Act & Assert
        with pytest.raises(AttributeError):
            script.content = "new code"
