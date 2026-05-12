from app.domain.value_objects.discrepancy import Discrepancy


def test_discrepancy_to_feedback_line_includes_severity_and_type():
    d = Discrepancy(
        feature_type="slot",
        severity="critical",
        description="中央スロット欠落",
        expected="長穴あり",
        actual="長穴なし",
    )
    line = d.to_feedback_line()
    assert "critical" in line
    assert "slot" in line
    assert "中央スロット欠落" in line
    assert "長穴あり" in line
    assert "長穴なし" in line


def test_discrepancy_default_confidence():
    d = Discrepancy(
        feature_type="hole", severity="major",
        description="x", expected="a", actual="b",
    )
    assert d.confidence == "high"
