import pytest
from unittest.mock import Mock

from app.usecase.generate_script_usecase import GenerateScriptUseCase
from app.domain.entities.design_intent import DesignIntent
from app.domain.entities.cad_model import GenerationStatus
from app.domain.value_objects.cad_script import CadScript
from app.domain.value_objects.design_step import DesignStep


class TestGenerateScriptUseCase:
    @pytest.fixture
    def mock_dependencies(self):
        """モック依存性を提供するフィクスチャ"""
        return {
            "cad_model_repo": Mock(),
            "script_generator": Mock(),
        }

    @pytest.fixture
    def usecase(self, mock_dependencies):
        """UseCaseインスタンスを生成するフィクスチャ"""
        return GenerateScriptUseCase(
            cad_model_repo=mock_dependencies["cad_model_repo"],
            script_generator=mock_dependencies["script_generator"],
        )

    def test_execute_success(self, mock_dependencies, usecase):
        """正常系: VLM スクリプト生成成功して CadScript を返す"""
        # Arrange
        model_id = "model-001"
        blueprint_id = "blueprint-001"

        mock_intent = DesignIntent(
            id="intent-001",
            blueprint_id=blueprint_id,
            steps=[
                DesignStep(
                    step_number=1,
                    instruction="厚さ10mmで押し出してベースを作る",
                )
            ],
        )

        mock_script = CadScript(
            content="from cadquery import Workplane\n# Generated code...",
            language="python",
        )

        mock_dependencies["script_generator"].generate.return_value = mock_script

        # Act
        result = usecase.execute(model_id, mock_intent)

        # Assert
        assert isinstance(result, CadScript)
        assert result.content is not None
        assert len(result.content) > 0
        assert result.language == "python"
        assert not result.is_empty()
        mock_dependencies["cad_model_repo"].update_status.assert_called_once_with(
            model_id, GenerationStatus.GENERATING
        )
        mock_dependencies["script_generator"].generate.assert_called_once_with(
            mock_intent
        )

    def test_execute_script_generation_failure(self, mock_dependencies, usecase):
        """異常系: VLM スクリプト生成失敗"""
        # Arrange
        model_id = "model-001"
        blueprint_id = "blueprint-001"

        mock_intent = DesignIntent(
            id="intent-001",
            blueprint_id=blueprint_id,
            steps=[],
        )

        mock_dependencies["script_generator"].generate.side_effect = Exception(
            "Script generation failed"
        )

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            usecase.execute(model_id, mock_intent)

        assert "Script generation failed" in str(exc_info.value)
