"""Verifier 共通の JSON 応答パース。

Anthropic / OpenAI どちらも同じ JSON スキーマで返すため、
ここに parser を集約してテストもしやすくする。
"""
from __future__ import annotations

import json
import re
from typing import Any

from loguru import logger

from app.domain.value_objects.discrepancy import Discrepancy
from app.domain.value_objects.verification import VerificationResult


_FENCE_RE = re.compile(r"```(?:json)?\s*\n(.*?)```", re.DOTALL)


def _extract_json(text: str) -> str:
    fence = _FENCE_RE.search(text)
    if fence:
        return fence.group(1).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        return text[start : end + 1]
    return text.strip()


def _coerce_str(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value
    return None


def parse_verifier_response(text: str) -> VerificationResult:
    """VLM の応答テキストから VerificationResult を組み立てる。"""
    try:
        data: dict[str, Any] = json.loads(_extract_json(text))
    except json.JSONDecodeError as e:
        logger.warning(f"[verifier] JSON parse failed: {e}; head={text[:160]}")
        return VerificationResult(is_valid=False)

    raw_list = data.get("discrepancies", []) or []
    discrepancies: list[Discrepancy] = []
    for raw in raw_list:
        if not isinstance(raw, dict):
            continue
        try:
            discrepancies.append(Discrepancy(
                feature_type=raw.get("feature_type", "other"),
                severity=raw.get("severity", "minor"),
                description=str(raw.get("description", "")),
                expected=str(raw.get("expected", "")),
                actual=str(raw.get("actual", "")),
                confidence=raw.get("confidence", "high"),
                location_hint=_coerce_str(raw.get("location_hint")),
                dimension_hint=_coerce_str(raw.get("dimension_hint")),
            ))
        except Exception as e:
            logger.warning(f"[verifier] skip malformed discrepancy: {raw} ({e})")
    return VerificationResult.from_discrepancies(tuple(discrepancies))
