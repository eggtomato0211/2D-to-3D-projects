import pytest
from unittest.mock import Mock, patch

from app.usecase.analyze_blueprint_usecase import AnalyzeBlueprintUseCase
from app.domain.entities.design_intent import DesignIntent
from app.domain.entities.cad_model import CADModel, GenerationStatus
from app.domain.entities.blueprint import Blueprint
from app.domain.value_objects.design_step import DesignStep


class TestAnalyzeBlueprintUseCase:
    @pytest.fixture
    def mock_dependencies(self):
        """モック依存性を提供するフィクスチャ"""
        return {
            "blueprint_repo": Mock(),
            "cad_model_repo": Mock(),
            "blueprint_analyzer": Mock(),
        }

    @pytest.fixture
    def usecase(self, mock_dependencies):
        """UseCaseインスタンスを生成するフィクスチャ"""
        return AnalyzeBlueprintUseCase(
            blueprint_repo=mock_dependencies["blueprint_repo"],
            cad_model_repo=mock_dependencies["cad_model_repo"],
            blueprint_analyzer=mock_dependencies["blueprint_analyzer"],
        )

    def test_execute_success(self, mock_dependencies, usecase):
        """正常系: VLM解析成功して DesignIntent を返す"""
        # Arrange
        model_id = "model-001"
        blueprint_id = "blueprint-001"

        mock_cad_model = CADModel(
            id=model_id,
            blueprint_id=blueprint_id,
            status=GenerationStatus.PENDING,
        )
        mock_blueprint = Blueprint(
            id=blueprint_id,
            file_path="/path/to/image.png",
            file_name="image.png",
        )
        mock_steps = [
            DesignStep(
                step_number=1,
                instruction="厚さ10mmで押し出してベースを作る",
            )
        ]

        mock_dependencies["cad_model_repo"].get_by_id.return_value = mock_cad_model
        mock_dependencies["blueprint_repo"].get_by_id.return_value = mock_blueprint
        mock_dependencies["blueprint_analyzer"].analyze.return_value = mock_steps

        # Act
        result = usecase.execute(model_id)

        # Assert
        assert isinstance(result, DesignIntent)
        assert result.id is not None
        assert len(result.id) > 0  # UUID形式
        assert result.blueprint_id == blueprint_id
        assert result.steps == mock_steps
        assert len(result.steps) == 1
        mock_dependencies["cad_model_repo"].update_status.assert_called_once_with(
            model_id, GenerationStatus.ANALYZING
        )
        mock_dependencies["blueprint_repo"].get_by_id.assert_called_once_with(
            blueprint_id
        )
        mock_dependencies["blueprint_analyzer"].analyze.assert_called_once_with(
            mock_blueprint
        )

    def test_execute_blueprint_not_found(self, mock_dependencies, usecase):
        """異常系: Blueprint が見つからない"""
        # Arrange
        model_id = "model-001"
        blueprint_id = "blueprint-001"

        mock_cad_model = CADModel(
            id=model_id,
            blueprint_id=blueprint_id,
            status=GenerationStatus.PENDING,
        )

        mock_dependencies["cad_model_repo"].get_by_id.return_value = mock_cad_model
        mock_dependencies["blueprint_repo"].get_by_id.side_effect = Exception(
            "Blueprint not found"
        )

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            usecase.execute(model_id)

        assert "Blueprint not found" in str(exc_info.value)
