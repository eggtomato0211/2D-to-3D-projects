import pytest

from app.domain.value_objects.discrepancy import Discrepancy


class TestDiscrepancy:
    def test_required_fields_are_set(self):
        d = Discrepancy(
            feature_type="hole",
            severity="critical",
            description="missing hole",
            expected="φ4.5 thru",
            actual="no hole",
        )

        assert d.feature_type == "hole"
        assert d.severity == "critical"
        assert d.confidence == "high"  # default
        assert d.location_hint is None
        assert d.dimension_hint is None

    def test_optional_hints(self):
        d = Discrepancy(
            feature_type="slot",
            severity="major",
            description="slot too narrow",
            expected="5 mm",
            actual="3 mm",
            confidence="medium",
            location_hint="center top",
            dimension_hint="5 × 14",
        )

        assert d.location_hint == "center top"
        assert d.dimension_hint == "5 × 14"
        assert d.confidence == "medium"

    def test_is_frozen(self):
        d = Discrepancy(
            feature_type="hole",
            severity="minor",
            description="",
            expected="",
            actual="",
        )

        with pytest.raises(AttributeError):
            d.severity = "critical"  # type: ignore[misc]
