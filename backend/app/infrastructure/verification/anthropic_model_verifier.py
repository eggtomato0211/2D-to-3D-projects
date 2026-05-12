"""Anthropic Claude を使った検証エンジン。

入力: 元 2D 図面 1 枚 + 線画 4 視点 + 影付き 4 視点 = 計 9 枚
出力: VerificationResult（Discrepancy[] を含む）
"""
from __future__ import annotations

from anthropic import Anthropic
from loguru import logger

from app.domain.interfaces.model_verifier import IModelVerifier
from app.domain.value_objects.four_view_image import FourViewImage
from app.domain.value_objects.verification import VerificationResult
from app.infrastructure.vlm.anthropic._image_blocks import (
    image_file_block,
    png_bytes_block,
)

from ._parsing import parse_verifier_response
from .prompts import P4_SYSTEM, P4_USER_TEXT

DEFAULT_MODEL = "claude-opus-4-7"
MAX_TOKENS = 2048


class AnthropicModelVerifier(IModelVerifier):

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL) -> None:
        self._client = Anthropic(api_key=api_key)
        self._model = model

    def verify(
        self,
        blueprint_image_path: str,
        line_views: FourViewImage,
        shaded_views: FourViewImage,
    ) -> VerificationResult:
        content = self._build_content(blueprint_image_path, line_views, shaded_views)
        msg = self._client.messages.create(
            model=self._model,
            max_tokens=MAX_TOKENS,
            system=P4_SYSTEM,
            messages=[{"role": "user", "content": content}],
        )
        text = "".join(b.text for b in msg.content if hasattr(b, "text"))
        logger.info(
            f"[verify] model={self._model} "
            f"in={msg.usage.input_tokens} out={msg.usage.output_tokens}"
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
            image_file_block(blueprint_image_path),
            {"type": "text", "text": "## candidate — line drawings (top, front, side, iso)"},
        ]
        content.extend(png_bytes_block(p) for p in line_views.as_list())
        content.append({
            "type": "text",
            "text": "## candidate — shaded renderings (top, front, side, iso)",
        })
        content.extend(png_bytes_block(p) for p in shaded_views.as_list())
        content.append({"type": "text", "text": P4_USER_TEXT})
        return content
