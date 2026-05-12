"""OpenAI Chat Completions API を使った検証エンジン。

入力: 元図面 1 枚 + 線画 4 視点 + 影付き 4 視点 = 計 9 枚（base64 画像）
出力: VerificationResult（Discrepancy のリスト）

AnthropicModelVerifier と同じ system prompt（P4_SYSTEM）を使い、
返り値も同じスキーマに揃える。
"""
from __future__ import annotations

import base64
import json
import re
from pathlib import Path
from typing import Any

from loguru import logger
from openai import OpenAI

from app.domain.interfaces.model_verifier import IModelVerifier
from app.domain.value_objects.discrepancy import Discrepancy
from app.domain.value_objects.four_view_image import FourViewImage
from app.domain.value_objects.verification import VerificationResult
from app.infrastructure.vlm.openai._retry import (
    SDK_MAX_RETRIES, SDK_TIMEOUT, call_with_retry,
)

from .prompts import P4_SYSTEM, P4_USER_TEXT

DEFAULT_MODEL = "gpt-5"
MAX_TOKENS = 4096


class OpenAIModelVerifier(IModelVerifier):
    """OpenAI のマルチモーダル Chat Completions API で 図面 vs 4視点レンダを比較。"""

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL) -> None:
        self._client = OpenAI(
            api_key=api_key,
            max_retries=SDK_MAX_RETRIES,
            timeout=SDK_TIMEOUT,
        )
        self._model = model

    def _is_reasoning_model(self) -> bool:
        m = self._model.lower()
        return m.startswith("gpt-5") or m.startswith("o3") or m.startswith("o4")

    # ---- IModelVerifier ----
    def verify(
        self,
        blueprint_image_path: str,
        line_views: FourViewImage,
        shaded_views: FourViewImage,
    ) -> VerificationResult:
        content = self._build_message_content(
            blueprint_image_path, line_views, shaded_views
        )
        common_kwargs = dict(
            model=self._model,
            messages=[
                {"role": "system", "content": P4_SYSTEM},
                {"role": "user", "content": content},
            ],
            response_format={"type": "json_object"},
        )
        # gpt-5 系は reasoning_effort を low に（出力予算を確保）
        if self._is_reasoning_model():
            common_kwargs["reasoning_effort"] = "low"

        def _do_call():
            try:
                return self._client.chat.completions.create(
                    **common_kwargs, max_completion_tokens=MAX_TOKENS,
                )
            except TypeError:
                common_kwargs.pop("reasoning_effort", None)
                return self._client.chat.completions.create(
                    **common_kwargs, max_tokens=MAX_TOKENS,
                )

        resp = call_with_retry(_do_call)
        text = resp.choices[0].message.content or ""
        usage = resp.usage
        logger.info(
            f"[verify-openai] model={self._model} "
            f"in={usage.prompt_tokens} out={usage.completion_tokens}"
        )
        return self._parse_response(text)

    # ---- internal ----
    @staticmethod
    def _image_block(png_bytes: bytes) -> dict:
        b64 = base64.b64encode(png_bytes).decode("ascii")
        return {
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{b64}"},
        }

    @classmethod
    def _file_to_image_block(cls, path: str) -> dict:
        p = Path(path)
        png_bytes = p.read_bytes()
        return cls._image_block(png_bytes)

    @classmethod
    def _build_message_content(
        cls,
        blueprint_image_path: str,
        line_views: FourViewImage,
        shaded_views: FourViewImage,
    ) -> list[dict]:
        content: list[dict] = []
        content.append({"type": "text", "text": "## reference (original 2D drawing)"})
        content.append(cls._file_to_image_block(blueprint_image_path))
        content.append({"type": "text",
                        "text": "## candidate — line drawings (top, front, side, iso)"})
        for png in line_views.as_list():
            content.append(cls._image_block(png))
        content.append({"type": "text",
                        "text": "## candidate — shaded renderings (top, front, side, iso)"})
        for png in shaded_views.as_list():
            content.append(cls._image_block(png))
        content.append({"type": "text", "text": P4_USER_TEXT})
        return content

    # ---- response parsing（Anthropic 版と同等）----
    @staticmethod
    def _extract_json(text: str) -> str:
        m = re.search(r"```(?:json)?\s*\n(.*?)```", text, re.DOTALL)
        if m:
            return m.group(1).strip()
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return text[start: end + 1]
        return text.strip()

    @classmethod
    def _parse_response(cls, text: str) -> VerificationResult:
        try:
            data: dict[str, Any] = json.loads(cls._extract_json(text))
        except json.JSONDecodeError as e:
            logger.warning(
                f"[verify-openai] JSON parse failed: {e}; raw head: {text[:200]}"
            )
            return VerificationResult.failure(
                feedback="JSON parse failed",
                discrepancies=tuple(),
                raw_response=text,
            )

        raw_list = data.get("discrepancies", []) or []
        discrepancies: list[Discrepancy] = []
        for raw in raw_list:
            if not isinstance(raw, dict):
                continue
            try:
                loc = raw.get("location_hint")
                dim = raw.get("dimension_hint")
                d = Discrepancy(
                    feature_type=raw.get("feature_type", "other"),
                    severity=raw.get("severity", "minor"),
                    description=str(raw.get("description", "")),
                    expected=str(raw.get("expected", "")),
                    actual=str(raw.get("actual", "")),
                    confidence=raw.get("confidence", "high"),
                    location_hint=str(loc) if isinstance(loc, str) and loc.strip() else None,
                    dimension_hint=str(dim) if isinstance(dim, str) and dim.strip() else None,
                )
                discrepancies.append(d)
            except Exception as e:
                logger.warning(f"[verify-openai] skip malformed discrepancy: {raw} ({e})")
                continue

        critical_count = sum(1 for d in discrepancies if d.severity == "critical")
        is_valid = critical_count == 0
        feedback = "\n".join(d.to_feedback_line() for d in discrepancies) or None

        return VerificationResult(
            is_valid=is_valid,
            discrepancies=tuple(discrepancies),
            feedback=feedback,
            raw_response=text,
        )
