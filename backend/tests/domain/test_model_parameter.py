import pytest

from app.domain.value_objects.model_parameter import ModelParameter, ParameterType


class TestModelParameter:
    def test_create_length_parameter(self):
        param = ModelParameter(
            name="Length_1",
            value=50.0,
            parameter_type=ParameterType.LENGTH,
        )
        assert param.name == "Length_1"
        assert param.value == 50.0
        assert param.parameter_type == ParameterType.LENGTH

    def test_create_radius_parameter(self):
        param = ModelParameter(
            name="Radius_1",
            value=10.5,
            parameter_type=ParameterType.RADIUS,
        )
        assert param.value == 10.5
        assert param.parameter_type == ParameterType.RADIUS

    def test_frozen(self):
        param = ModelParameter(name="L1", value=1.0, parameter_type=ParameterType.LENGTH)
        with pytest.raises(AttributeError):
            param.value = 2.0

    def test_empty_name_raises(self):
        with pytest.raises(ValueError, match="name"):
            ModelParameter(name="", value=1.0, parameter_type=ParameterType.LENGTH)

    def test_negative_value_raises(self):
        with pytest.raises(ValueError, match="value"):
            ModelParameter(name="L1", value=-1.0, parameter_type=ParameterType.LENGTH)

    def test_zero_value_allowed(self):
        param = ModelParameter(name="L1", value=0.0, parameter_type=ParameterType.LENGTH)
        assert param.value == 0.0
