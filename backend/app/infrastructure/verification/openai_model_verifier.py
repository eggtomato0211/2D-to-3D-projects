"""OpenAI Chat Completions API を使った検証エンジン。

入力: 元 2D 図面 1 枚 + 線画 4 視点 + 影付き 4 視点 = 計 9 枚
出力: VerificationResult（Anthropic 版と同じスキーマ）
"""
from __future__ import annotations

import base64
from pathlib import Path

from loguru import logger
from openai import OpenAI

from app.domain.interfaces.model_verifier import IModelVerifier
from app.domain.value_objects.four_view_image import FourViewImage
from app.domain.value_objects.verification import VerificationResult
from app.infrastructure.vlm.openai._retry import (
    SDK_MAX_RETRIES,
    SDK_TIMEOUT,
    call_with_retry,
)

from ._parsing import parse_verifier_response
from .prompts import P4_SYSTEM, P4_USER_TEXT

DEFAULT_MODEL = "gpt-5"
MAX_TOKENS = 4096


def _image_block(png_bytes: bytes) -> dict:
    b64 = base64.b64encode(png_bytes).decode("ascii")
    return {
        "type": "image_url",
        "image_url": {"url": f"data:image/png;base64,{b64}"},
    }


def _image_file_block(path: str) -> dict:
    return _image_block(Path(path).read_bytes())


class OpenAIModelVerifier(IModelVerifier):

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

    def verify(
        self,
        blueprint_image_path: str,
        line_views: FourViewImage,
        shaded_views: FourViewImage,
    ) -> VerificationResult:
        content = self._build_content(blueprint_image_path, line_views, shaded_views)
        kwargs: dict = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": P4_SYSTEM},
                {"role": "user", "content": content},
            ],
            "response_format": {"type": "json_object"},
        }
        if self._is_reasoning_model():
            kwargs["reasoning_effort"] = "low"

        def _call():
            try:
                return self._client.chat.completions.create(
                    **kwargs, max_completion_tokens=MAX_TOKENS,
                )
            except TypeError:
                kwargs.pop("reasoning_effort", None)
                return self._client.chat.completions.create(
                    **kwargs, max_tokens=MAX_TOKENS,
                )

        resp = call_with_retry(_call)
        text = resp.choices[0].message.content or ""
        usage = resp.usage
        logger.info(
            f"[verify-openai] model={self._model} "
            f"in={usage.prompt_tokens} out={usage.completion_tokens}"
        )
        return parse_verifier_response(text)

    @staticmethod
    def _build_content(
        blueprint_image_path: str,
        line_views: FourViewImage,
        shaded_views: FourViewImage,
    ) -> list[dict]:
        content: list[dict] = [
            {"type": "text", "text": "## reference (original 2D drawing)"},
            _image_file_block(blueprint_image_path),
            {"type": "text", "text": "## candidate — line drawings (top, front, side, iso)"},
        ]
        content.extend(_image_block(p) for p in line_views.as_list())
        content.append({
            "type": "text",
            "text": "## candidate — shaded renderings (top, front, side, iso)",
        })
        content.extend(_image_block(p) for p in shaded_views.as_list())
        content.append({"type": "text", "text": P4_USER_TEXT})
        return content
