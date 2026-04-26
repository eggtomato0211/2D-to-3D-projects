from app.domain.entities.blueprint import Blueprint


class TestBlueprint:
    def test_create_with_required_fields(self):
        # Arrange
        id = "bp-001"
        file_path = "/uploads/drawing.png"
        file_name = "drawing.png"

        # Act
        bp = Blueprint(id=id, file_path=file_path, file_name=file_name)

        # Assert
        assert bp.id == "bp-001"
        assert bp.file_path == "/uploads/drawing.png"
        assert bp.file_name == "drawing.png"
        assert bp.content_type == "image/png"
