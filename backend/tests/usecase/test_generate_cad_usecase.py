import pytest
from unittest.mock import Mock

from app.usecase.generate_cad_usecase import GenerateCadUseCase
from app.domain.entities.cad_model import CADModel, GenerationStatus
from app.domain.entities.design_intent import DesignIntent
from app.domain.value_objects.cad_script import CadScript
from app.domain.value_objects.design_step import DesignStep


class TestGenerateCadUseCase:
    @pytest.fixture
    def mock_usecases(self):
        return {
            "analyze": Mock(),
            "generate_script": Mock(),
            "execute_script": Mock(),
            "script_generator": Mock(),
        }

    @pytest.fixture
    def usecase(self, mock_usecases):
        return GenerateCadUseCase(
            analyze_usecase=mock_usecases["analyze"],
            generate_script_usecase=mock_usecases["generate_script"],
            execute_script_usecase=mock_usecases["execute_script"],
            script_generator=mock_usecases["script_generator"],
        )

    def test_execute_success(self, mock_usecases, usecase):
        """正常系: 3ステップが順に実行され CADModel が返る"""
        # Arrange
        model_id = "model-001"

        mock_intent = DesignIntent(
            id="intent-001",
            blueprint_id="blueprint-001",
            steps=[
                DesignStep(
                    step_number=1,
                    instruction="厚さ10mmで押し出してベースを作る",
                )
            ],
        )
        mock_script = CadScript(
            content="from cadquery import Workplane\n# Code...",
            language="python",
        )
        mock_cad_model = CADModel(
            id=model_id,
            blueprint_id="blueprint-001",
            status=GenerationStatus.SUCCESS,
            stl_path="/path/to/output.stl",
        )

        mock_usecases["analyze"].execute.return_value = mock_intent
        mock_usecases["generate_script"].execute.return_value = mock_script
        mock_usecases["execute_script"].execute.return_value = mock_cad_model

        # Act
        result = usecase.execute(model_id)

        # Assert
        assert isinstance(result, CADModel)
        assert result.status == GenerationStatus.SUCCESS
        assert result.stl_path == "/path/to/output.stl"
        mock_usecases["analyze"].execute.assert_called_once_with(model_id)
        mock_usecases["generate_script"].execute.assert_called_once_with(
            model_id, mock_intent
        )
        mock_usecases["execute_script"].execute.assert_called_once_with(
            model_id, mock_script
        )

    def test_execute_stops_on_analyze_failure(self, mock_usecases, usecase):
        """異常系: Step 1 失敗時に Step 2, 3 が呼ばれない"""
        # Arrange
        model_id = "model-001"
        mock_usecases["analyze"].execute.side_effect = Exception("VLM analysis failed")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            usecase.execute(model_id)

        assert "VLM analysis failed" in str(exc_info.value)
        mock_usecases["generate_script"].execute.assert_not_called()
        mock_usecases["execute_script"].execute.assert_not_called()

    def test_execute_stops_on_generate_failure(self, mock_usecases, usecase):
        """異常系: Step 2 失敗時に Step 3 が呼ばれない"""
        # Arrange
        model_id = "model-001"

        mock_intent = DesignIntent(
            id="intent-001",
            blueprint_id="blueprint-001",
            steps=[],
        )

        mock_usecases["analyze"].execute.return_value = mock_intent
        mock_usecases["generate_script"].execute.side_effect = Exception(
            "Script generation failed"
        )

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            usecase.execute(model_id)

        assert "Script generation failed" in str(exc_info.value)
        mock_usecases["execute_script"].execute.assert_not_called()

    def test_execute_retries_on_script_execution_error(self, mock_usecases, usecase):
        """異常系: Step 3 失敗時にエラー修正ループでリトライする"""
        model_id = "model-001"

        mock_intent = DesignIntent(
            id="intent-001",
            blueprint_id="blueprint-001",
            steps=[DesignStep(step_number=1, instruction="押し出し")],
        )
        bad_script = CadScript(content="bad code", language="python")
        fixed_script = CadScript(content="fixed code", language="python")

        failed_model = CADModel(
            id=model_id,
            blueprint_id="blueprint-001",
            status=GenerationStatus.FAILED,
            error_message="Selected faces must be co-planar.",
        )
        success_model = CADModel(
            id=model_id,
            blueprint_id="blueprint-001",
            status=GenerationStatus.SUCCESS,
            stl_path="/path/to/output.stl",
        )

        mock_usecases["analyze"].execute.return_value = mock_intent
        mock_usecases["generate_script"].execute.return_value = bad_script
        mock_usecases["execute_script"].execute.side_effect = [failed_model, success_model]
        mock_usecases["script_generator"].fix_script.return_value = fixed_script

        result = usecase.execute(model_id)

        assert result.status == GenerationStatus.SUCCESS
        mock_usecases["script_generator"].fix_script.assert_called_once_with(
            bad_script, "Selected faces must be co-planar."
        )
        assert mock_usecases["execute_script"].execute.call_count == 2

    def test_execute_gives_up_after_max_retries(self, mock_usecases, usecase):
        """異常系: 最大リトライ回数を超えたら FAILED で返す"""
        model_id = "model-001"

        mock_intent = DesignIntent(
            id="intent-001",
            blueprint_id="blueprint-001",
            steps=[DesignStep(step_number=1, instruction="押し出し")],
        )
        bad_script = CadScript(content="bad code", language="python")

        failed_model = CADModel(
            id=model_id,
            blueprint_id="blueprint-001",
            status=GenerationStatus.FAILED,
            error_message="Persistent error",
        )

        mock_usecases["analyze"].execute.return_value = mock_intent
        mock_usecases["generate_script"].execute.return_value = bad_script
        mock_usecases["execute_script"].execute.return_value = failed_model
        mock_usecases["script_generator"].fix_script.return_value = bad_script

        result = usecase.execute(model_id)

        assert result.status == GenerationStatus.FAILED
        assert mock_usecases["script_generator"].fix_script.call_count == 5
