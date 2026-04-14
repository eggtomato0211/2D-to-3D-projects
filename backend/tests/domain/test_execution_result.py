import pytest

from app.domain.value_objects.execution_result import ExecutionResult
from app.domain.value_objects.model_parameter import ModelParameter, ParameterType


class TestExecutionResult:
    def test_create_with_parameters(self):
        params = [
            ModelParameter(name="Length_1", value=50.0, parameter_type=ParameterType.LENGTH),
            ModelParameter(name="Radius_1", value=10.0, parameter_type=ParameterType.RADIUS),
        ]
        result = ExecutionResult(stl_filename="abc.stl", parameters=params)
        assert result.stl_filename == "abc.stl"
        assert len(result.parameters) == 2

    def test_create_without_parameters(self):
        result = ExecutionResult(stl_filename="abc.stl")
        assert result.parameters == []

    def test_empty_filename_raises(self):
        with pytest.raises(ValueError, match="stl_filename"):
            ExecutionResult(stl_filename="")

    def test_frozen(self):
        result = ExecutionResult(stl_filename="abc.stl")
        with pytest.raises(AttributeError):
            result.stl_filename = "other.stl"
