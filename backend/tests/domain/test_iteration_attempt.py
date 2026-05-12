import pytest

from app.domain.value_objects.discrepancy import Discrepancy
from app.domain.value_objects.iteration_attempt import IterationAttempt


def _disc(severity: str) -> Discrepancy:
    return Discrepancy(
        feature_type="hole",
        severity=severity,  # type: ignore[arg-type]
        description="",
        expected="",
        actual="",
    )


def test_iteration_attempt_keeps_tried_and_remaining():
    a = IterationAttempt(
        iteration=2,
        tried=(_disc("critical"),),
        remaining=(_disc("minor"),),
    )

    assert a.iteration == 2
    assert len(a.tried) == 1
    assert len(a.remaining) == 1


def test_iteration_attempt_is_frozen():
    a = IterationAttempt(iteration=1, tried=(), remaining=())

    with pytest.raises(AttributeError):
        a.iteration = 5  # type: ignore[misc]
