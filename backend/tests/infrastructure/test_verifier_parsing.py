"""共有パーサ `parse_verifier_response` の単体テスト。"""
from app.infrastructure.verification._parsing import parse_verifier_response


def test_parse_returns_success_for_empty_discrepancies():
    text = '```json\n{"discrepancies": []}\n```'

    result = parse_verifier_response(text)

    assert result.is_valid is True
    assert result.discrepancies == ()


def test_parse_returns_invalid_when_critical_present():
    text = """```json
{
  "discrepancies": [
    {
      "feature_type": "hole",
      "severity": "critical",
      "description": "missing thru hole",
      "expected": "φ4.5 thru",
      "actual": "no hole",
      "confidence": "high",
      "location_hint": "PCD φ42",
      "dimension_hint": "φ4.5"
    }
  ]
}
```"""

    result = parse_verifier_response(text)

    assert result.is_valid is False
    assert result.critical_count() == 1
    d = result.discrepancies[0]
    assert d.location_hint == "PCD φ42"
    assert d.dimension_hint == "φ4.5"


def test_parse_handles_unfenced_json():
    text = '{"discrepancies": [{"feature_type":"slot","severity":"major","description":"","expected":"","actual":""}]}'

    result = parse_verifier_response(text)

    assert result.major_count() == 1
    assert result.is_valid is True  # critical=0


def test_parse_returns_invalid_on_unparseable_text():
    result = parse_verifier_response("this is not json at all")

    assert result.is_valid is False
    assert result.discrepancies == ()


def test_parse_treats_empty_strings_as_none_hints():
    text = """```json
{
  "discrepancies": [
    {
      "feature_type": "hole", "severity": "minor",
      "description": "x", "expected": "x", "actual": "x",
      "location_hint": "", "dimension_hint": null
    }
  ]
}
```"""

    result = parse_verifier_response(text)
    d = result.discrepancies[0]
    assert d.location_hint is None
    assert d.dimension_hint is None
