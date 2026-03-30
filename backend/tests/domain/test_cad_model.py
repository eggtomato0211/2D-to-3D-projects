from app.domain.entities.cad_model import CADModel, GenerationStatus

class TestCADModel:
    def test_create_with_required_fields(self):
        # Arrange
        id = "cad-001"
        blueprint_id = "bp-001"
        status = GenerationStatus.PENDING

        # Act
        cad_model = CADModel(id=id, blueprint_id=blueprint_id, status=status)

        # Assert
        assert cad_model.id == "cad-001"
        assert cad_model.blueprint_id == "bp-001"
        assert cad_model.status == GenerationStatus.PENDING
        assert cad_model.stl_path is None
        assert cad_model.error_message is None
    
    def test_create_with_all_fields(self):
        # Arrange & Act
        cad_model = CADModel(
            id="cad-002",
            blueprint_id="bp-002",
            status=GenerationStatus.SUCCESS,
            stl_path="/models/cad-002.stl",
            error_message=None,
        )

        # Assert
        assert cad_model.stl_path == "/models/cad-002.stl"
        assert cad_model.error_message is None
