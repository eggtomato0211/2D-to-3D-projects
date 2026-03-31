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
        assert bp.width is None
        assert bp.height is None

    def test_create_with_all_fields(self):
        # Arrange & Act
        bp = Blueprint(
            id="bp-002",
            file_path="/uploads/plan.png",
            file_name="plan.png",
            width=1920,
            height=1080,
        )

        # Assert
        assert bp.width == 1920
        assert bp.height == 1080
