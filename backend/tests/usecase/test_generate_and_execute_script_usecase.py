import pytest
from unittest.mock import Mock

from app.usecase.generate_and_execute_script_usecase import (
    GenerateAndExecuteScriptUseCase,
    MAX_FIX_ATTEMPTS,
)
from app.domain.entities.cad_model import CADModel, GenerationStatus
from app.domain.value_objects.cad_script import CadScript


class TestGenerateAndExecuteScriptUseCase:
    @pytest.fixture
    def mocks(self):
        return {
            "generate_script": Mock(),
            "execute_script": Mock(),
            "script_generator": Mock(),
        }

    @pytest.fixture
    def usecase(self, mocks):
        return GenerateAndExecuteScriptUseCase(
            generate_script_usecase=mocks["generate_script"],
            execute_script_usecase=mocks["execute_script"],
            script_generator=mocks["script_generator"],
        )

    def test_execute_success_on_first_try(self, mocks, usecase):
        """初回実行で成功すればリトライせずに返る"""
        model_id = "model-001"
        script = CadScript(content="code")
        success_model = CADModel(
            id=model_id,
            blueprint_id="bp-001",
            status=GenerationStatus.SUCCESS,
            stl_path="/path/to/output.stl",
        )

        mocks["generate_script"].execute.return_value = script
        mocks["execute_script"].execute.return_value = success_model

        result = usecase.execute(model_id)

        assert result is success_model
        mocks["generate_script"].execute.assert_called_once_with(model_id)
        mocks["execute_script"].execute.assert_called_once_with(model_id, script)
        mocks["script_generator"].fix_script.assert_not_called()

    def test_execute_retries_on_error(self, mocks, usecase):
        """失敗したら fix_script → 再実行を繰り返し、成功したら返る"""
        model_id = "model-001"
        bad_script = CadScript(content="bad")
        fixed_script = CadScript(content="fixed")

        failed_model = CADModel(
            id=model_id,
            blueprint_id="bp-001",
            status=GenerationStatus.FAILED,
            error_message="Selected faces must be co-planar.",
        )
        success_model = CADModel(
            id=model_id,
            blueprint_id="bp-001",
            status=GenerationStatus.SUCCESS,
            stl_path="/path/to/output.stl",
        )

        mocks["generate_script"].execute.return_value = bad_script
        mocks["execute_script"].execute.side_effect = [failed_model, success_model]
        mocks["script_generator"].fix_script.return_value = fixed_script

        result = usecase.execute(model_id)

        assert result.status == GenerationStatus.SUCCESS
        mocks["script_generator"].fix_script.assert_called_once_with(
            bad_script, "Selected faces must be co-planar."
        )
        assert mocks["execute_script"].execute.call_count == 2

    def test_execute_gives_up_after_max_retries(self, mocks, usecase):
        """MAX_FIX_ATTEMPTS 回失敗したら FAILED の CADModel を返す"""
        model_id = "model-001"
        bad_script = CadScript(content="bad")

        failed_model = CADModel(
            id=model_id,
            blueprint_id="bp-001",
            status=GenerationStatus.FAILED,
            error_message="Persistent error",
        )

        mocks["generate_script"].execute.return_value = bad_script
        mocks["execute_script"].execute.return_value = failed_model
        mocks["script_generator"].fix_script.return_value = bad_script

        result = usecase.execute(model_id)

        assert result.status == GenerationStatus.FAILED
        assert mocks["script_generator"].fix_script.call_count == MAX_FIX_ATTEMPTS
        # 初回 + MAX_FIX_ATTEMPTS 回のリトライ
        assert mocks["execute_script"].execute.call_count == MAX_FIX_ATTEMPTS + 1
