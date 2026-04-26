import pytest
from unittest.mock import Mock

from app.usecase.generate_script_usecase import GenerateScriptUseCase
from app.domain.entities.cad_model import CADModel, GenerationStatus
from app.domain.value_objects.cad_script import CadScript
from app.domain.value_objects.design_step import DesignStep


class TestGenerateScriptUseCase:
    @pytest.fixture
    def mock_dependencies(self):
        return {
            "cad_model_repo": Mock(),
            "script_generator": Mock(),
        }

    @pytest.fixture
    def usecase(self, mock_dependencies):
        return GenerateScriptUseCase(
            cad_model_repo=mock_dependencies["cad_model_repo"],
            script_generator=mock_dependencies["script_generator"],
        )

    def test_execute_success(self, mock_dependencies, usecase):
        """CADModel に保存された steps/clarifications でスクリプト生成に成功する"""
        # Arrange
        model_id = "model-001"
        blueprint_id = "blueprint-001"

        mock_steps = [
            DesignStep(
                step_number=1,
                instruction="厚さ10mmで押し出してベースを作る",
            )
        ]
        mock_cad_model = CADModel(
            id=model_id,
            blueprint_id=blueprint_id,
            status=GenerationStatus.ANALYZING,
            design_steps=mock_steps,
        )

        mock_script = CadScript(
            content="from cadquery import Workplane\n# Generated code...",
        )

        mock_dependencies["cad_model_repo"].get_by_id.return_value = mock_cad_model
        mock_dependencies["script_generator"].generate.return_value = mock_script

        # Act
        result = usecase.execute(model_id)

        # Assert
        assert isinstance(result, CadScript)
        assert result.content
        assert mock_cad_model.status == GenerationStatus.GENERATING
        mock_dependencies["cad_model_repo"].save.assert_called_once_with(mock_cad_model)
        mock_dependencies["script_generator"].generate.assert_called_once_with(
            mock_steps, []
        )

    def test_execute_script_generation_failure(self, mock_dependencies, usecase):
        """異常系: VLM スクリプト生成失敗"""
        # Arrange
        model_id = "model-001"
        mock_cad_model = CADModel(
            id=model_id,
            blueprint_id="blueprint-001",
            status=GenerationStatus.ANALYZING,
        )

        mock_dependencies["cad_model_repo"].get_by_id.return_value = mock_cad_model
        mock_dependencies["script_generator"].generate.side_effect = Exception(
            "Script generation failed"
        )

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            usecase.execute(model_id)

        assert "Script generation failed" in str(exc_info.value)
