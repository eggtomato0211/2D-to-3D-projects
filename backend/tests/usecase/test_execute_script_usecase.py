import pytest
from unittest.mock import Mock

from app.usecase.execute_script_usecase import ExecuteScriptUseCase
from app.domain.entities.cad_model import CADModel, GenerationStatus
from app.domain.value_objects.cad_script import CadScript


class TestExecuteScriptUseCase:
    @pytest.fixture
    def mock_dependencies(self):
        """モック依存性を提供するフィクスチャ"""
        return {
            "cad_model_repo": Mock(),
            "cad_executor": Mock(),
        }

    @pytest.fixture
    def usecase(self, mock_dependencies):
        """UseCaseインスタンスを生成するフィクスチャ"""
        return ExecuteScriptUseCase(
            cad_model_repo=mock_dependencies["cad_model_repo"],
            cad_executor=mock_dependencies["cad_executor"],
        )

    def test_execute_success(self, mock_dependencies, usecase):
        """正常系: スクリプト実行成功して STL ファイルを生成"""
        # Arrange
        model_id = "model-001"
        blueprint_id = "blueprint-001"
        stl_path = "/path/to/output.stl"

        mock_cad_model = CADModel(
            id=model_id,
            blueprint_id=blueprint_id,
            status=GenerationStatus.PENDING,
        )

        mock_script = CadScript(
            content="from cadquery import Workplane\n# Generated code...",
            language="python",
        )

        mock_dependencies["cad_model_repo"].get_by_id.return_value = mock_cad_model
        mock_dependencies["cad_executor"].execute.return_value = stl_path

        # Act
        result = usecase.execute(model_id, mock_script)

        # Assert
        assert isinstance(result, CADModel)
        assert result.status == GenerationStatus.SUCCESS
        assert result.stl_path == stl_path
        assert result.error_message is None
        mock_dependencies["cad_model_repo"].update_status.assert_called_once_with(
            model_id, GenerationStatus.EXECUTING
        )
        mock_dependencies["cad_model_repo"].update.assert_called_once()
        mock_dependencies["cad_executor"].execute.assert_called_once_with(mock_script)

    def test_execute_script_execution_failure(self, mock_dependencies, usecase):
        """異常系: スクリプト実行失敗"""
        # Arrange
        model_id = "model-001"
        blueprint_id = "blueprint-001"

        mock_cad_model = CADModel(
            id=model_id,
            blueprint_id=blueprint_id,
            status=GenerationStatus.PENDING,
        )

        mock_script = CadScript(
            content="invalid code...",
            language="python",
        )

        error_message = "Syntax error in CadQuery script"
        mock_dependencies["cad_model_repo"].get_by_id.return_value = mock_cad_model
        mock_dependencies["cad_executor"].execute.side_effect = Exception(
            error_message
        )

        # Act
        result = usecase.execute(model_id, mock_script)

        # Assert
        assert isinstance(result, CADModel)
        assert result.status == GenerationStatus.FAILED
        assert result.stl_path is None
        assert result.error_message == error_message
        mock_dependencies["cad_model_repo"].update.assert_called_once()

    def test_execute_updates_cad_model_in_repo(self, mock_dependencies, usecase):
        """実行後に CADModel がリポジトリに保存される"""
        # Arrange
        model_id = "model-001"
        blueprint_id = "blueprint-001"
        stl_path = "/path/to/output.stl"

        mock_cad_model = CADModel(
            id=model_id,
            blueprint_id=blueprint_id,
            status=GenerationStatus.PENDING,
        )

        mock_script = CadScript(
            content="from cadquery import Workplane\n# Code...",
            language="python",
        )

        mock_dependencies["cad_model_repo"].get_by_id.return_value = mock_cad_model
        mock_dependencies["cad_executor"].execute.return_value = stl_path

        # Act
        result = usecase.execute(model_id, mock_script)

        # Assert
        mock_dependencies["cad_model_repo"].update.assert_called_once()
        updated_model = mock_dependencies["cad_model_repo"].update.call_args[0][0]
        assert updated_model.status == GenerationStatus.SUCCESS
        assert updated_model.stl_path == stl_path
