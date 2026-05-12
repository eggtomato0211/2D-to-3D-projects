"""AnthropicModelVerifier の応答パース部のユニットテスト（API は呼ばない）。"""
from app.infrastructure.verification.anthropic_model_verifier import (
    AnthropicModelVerifier,
)


def test_parse_response_with_critical_returns_failure():
    text = """```json
{
  "discrepancies": [
    {
      "feature_type": "slot",
      "severity": "critical",
      "description": "中央スロット欠落",
      "expected": "長穴あり",
      "actual": "丸穴のみ",
      "confidence": "high"
    }
  ]
}
```"""
    result = AnthropicModelVerifier._parse_response(text)
    assert result.is_valid is False
    assert len(result.discrepancies) == 1
    d = result.discrepancies[0]
    assert d.feature_type == "slot"
    assert d.severity == "critical"
    assert "中央スロット" in d.description


def test_parse_response_with_empty_returns_success():
    text = '```json\n{"discrepancies": []}\n```'
    result = AnthropicModelVerifier._parse_response(text)
    assert result.is_valid is True
    assert result.discrepancies == ()


def test_parse_response_only_minors_keeps_discrepancies_but_valid():
    text = """```json
{
  "discrepancies": [
    {"feature_type": "chamfer", "severity": "minor",
     "description": "C0.5 missing", "expected": "C0.5", "actual": "none",
     "confidence": "medium"}
  ]
}
```"""
    result = AnthropicModelVerifier._parse_response(text)
    assert result.is_valid is True   # critical 無しなら is_valid=True
    # ただし minor 不一致は report 用に残す
    assert len(result.discrepancies) == 1
    assert result.discrepancies[0].severity == "minor"


def test_parse_response_invalid_json_falls_back_to_failure_with_raw():
    text = "this is not json at all"
    result = AnthropicModelVerifier._parse_response(text)
    assert result.is_valid is False
    assert result.raw_response == text


def test_extract_json_from_fenced_block():
    text = "前置きテキスト\n```json\n{\"a\": 1}\n```\n後置き"
    assert AnthropicModelVerifier._extract_json(text).strip() == '{"a": 1}'


def test_extract_json_from_unfenced_object():
    text = "  ノイズ {\"x\": 2} 末尾  "
    assert '"x"' in AnthropicModelVerifier._extract_json(text)
