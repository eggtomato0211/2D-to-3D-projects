import pytest
from unittest.mock import Mock

from app.usecase.generate_cad_usecase import GenerateCadUseCase
from app.domain.entities.cad_model import CADModel, GenerationStatus
from app.domain.value_objects.design_step import DesignStep


class TestGenerateCadUseCase:
    @pytest.fixture
    def mock_usecases(self):
        return {
            "analyze": Mock(),
            "generate_and_execute": Mock(),
        }

    @pytest.fixture
    def usecase(self, mock_usecases):
        return GenerateCadUseCase(
            analyze_usecase=mock_usecases["analyze"],
            generate_and_execute_usecase=mock_usecases["generate_and_execute"],
        )

    def _make_analyzed_model(
        self,
        model_id: str = "model-001",
        blueprint_id: str = "blueprint-001",
        clarifications: list | None = None,
        clarifications_confirmed: bool = True,
    ) -> CADModel:
        return CADModel(
            id=model_id,
            blueprint_id=blueprint_id,
            status=GenerationStatus.ANALYZING,
            design_steps=[
                DesignStep(step_number=1, instruction="厚さ10mmで押し出してベースを作る"),
            ],
            clarifications=clarifications or [],
            clarifications_confirmed=clarifications_confirmed,
        )

    def test_execute_success_delegates_to_generate_and_execute(
        self, mock_usecases, usecase
    ):
        """確認事項なしなら Step2+3 が呼ばれ結果が返る"""
        # Arrange
        model_id = "model-001"
        analyzed_model = self._make_analyzed_model(model_id)
        success_model = CADModel(
            id=model_id,
            blueprint_id="blueprint-001",
            status=GenerationStatus.SUCCESS,
            stl_path="/path/to/output.stl",
        )

        mock_usecases["analyze"].execute.return_value = analyzed_model
        mock_usecases["generate_and_execute"].execute.return_value = success_model

        # Act
        result = usecase.execute(model_id)

        # Assert
        assert result is success_model
        mock_usecases["analyze"].execute.assert_called_once_with(model_id)
        mock_usecases["generate_and_execute"].execute.assert_called_once_with(model_id)

    def test_execute_stops_when_clarifications_pending(self, mock_usecases, usecase):
        """確認事項が未回答なら Step 2+3 が呼ばれずに analyzed_model が返る"""
        # Arrange
        from app.domain.value_objects.clarification import Clarification

        model_id = "model-001"
        analyzed_model = self._make_analyzed_model(
            model_id,
            clarifications=[Clarification(id="clarification_1", question="厚みは?")],
            clarifications_confirmed=False,
        )
        mock_usecases["analyze"].execute.return_value = analyzed_model

        # Act
        result = usecase.execute(model_id)

        # Assert
        assert result is analyzed_model
        mock_usecases["generate_and_execute"].execute.assert_not_called()

    def test_execute_stops_on_analyze_failure(self, mock_usecases, usecase):
        """Step 1 失敗時に Step 2+3 が呼ばれない"""
        # Arrange
        model_id = "model-001"
        mock_usecases["analyze"].execute.side_effect = Exception("VLM analysis failed")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            usecase.execute(model_id)

        assert "VLM analysis failed" in str(exc_info.value)
        mock_usecases["generate_and_execute"].execute.assert_not_called()
