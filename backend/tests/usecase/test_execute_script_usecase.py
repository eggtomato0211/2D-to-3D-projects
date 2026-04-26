import pytest
from unittest.mock import Mock

from app.usecase.execute_script_usecase import ExecuteScriptUseCase
from app.domain.entities.cad_model import CADModel, GenerationStatus
from app.domain.value_objects.cad_script import CadScript
from app.domain.value_objects.execution_result import ExecutionResult
from app.domain.value_objects.model_parameter import ModelParameter, ParameterType


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
        stl_filename = "output.stl"
        params = [
            ModelParameter(name="Length_1", value=50.0, parameter_type=ParameterType.LENGTH),
        ]
        execution_result = ExecutionResult(stl_filename=stl_filename, parameters=params)

        mock_cad_model = CADModel(
            id=model_id,
            blueprint_id=blueprint_id,
            status=GenerationStatus.PENDING,
        )

        mock_script = CadScript(
            content="from cadquery import Workplane\n# Generated code...",
        )

        mock_dependencies["cad_model_repo"].get_by_id.return_value = mock_cad_model
        mock_dependencies["cad_executor"].execute.return_value = execution_result

        # Act
        result = usecase.execute(model_id, mock_script)

        # Assert
        assert isinstance(result, CADModel)
        assert result.status == GenerationStatus.SUCCESS
        assert result.stl_path == stl_filename
        assert result.parameters == params
        assert result.error_message is None
        # 1 回目: status=EXECUTING、2 回目: 実行結果反映後
        assert mock_dependencies["cad_model_repo"].save.call_count == 2
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
        assert mock_dependencies["cad_model_repo"].save.call_count == 2

    def test_execute_updates_cad_model_in_repo(self, mock_dependencies, usecase):
        """実行後に CADModel がリポジトリに保存される"""
        # Arrange
        model_id = "model-001"
        blueprint_id = "blueprint-001"
        stl_filename = "output.stl"
        execution_result = ExecutionResult(stl_filename=stl_filename)

        mock_cad_model = CADModel(
            id=model_id,
            blueprint_id=blueprint_id,
            status=GenerationStatus.PENDING,
        )

        mock_script = CadScript(
            content="from cadquery import Workplane\n# Code...",
        )

        mock_dependencies["cad_model_repo"].get_by_id.return_value = mock_cad_model
        mock_dependencies["cad_executor"].execute.return_value = execution_result

        # Act
        result = usecase.execute(model_id, mock_script)

        # Assert
        save_calls = mock_dependencies["cad_model_repo"].save.call_args_list
        assert len(save_calls) == 2
        final_model = save_calls[-1][0][0]
        assert final_model.status == GenerationStatus.SUCCESS
        assert final_model.stl_path == stl_filename
