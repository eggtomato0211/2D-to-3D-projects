"""Anthropic Claude を使った検証エンジン（Phase 2-γ）。

入力: 元図面 1 枚 + 線画 4 視点 + 影付き 4 視点 = 計 9 枚
出力: 構造化された Discrepancy のリスト
"""
from __future__ import annotations

import json
import re
from typing import Any

from anthropic import Anthropic
from loguru import logger

from app.domain.interfaces.model_verifier import IModelVerifier
from app.domain.value_objects.discrepancy import Discrepancy
from app.domain.value_objects.four_view_image import FourViewImage
from app.domain.value_objects.verification import VerificationResult
from app.infrastructure.vlm.anthropic._image_blocks import (
    image_file_block,
    png_bytes_block,
)

from .prompts import P4_SYSTEM, P4_USER_TEXT

DEFAULT_MODEL = "claude-opus-4-7"
MAX_TOKENS = 2048


class AnthropicModelVerifier(IModelVerifier):
    """Claude (Opus 4.7 デフォルト) で図面 vs 4視点レンダを比較し Discrepancy を抽出。"""

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL) -> None:
        self._client = Anthropic(api_key=api_key)
        self._model = model

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
        msg = self._client.messages.create(
            model=self._model,
            max_tokens=MAX_TOKENS,
            system=P4_SYSTEM,
            messages=[{"role": "user", "content": content}],
        )
        text = "".join(b.text for b in msg.content if hasattr(b, "text"))
        logger.info(
            f"[verify] model={self._model} in={msg.usage.input_tokens} "
            f"out={msg.usage.output_tokens}"
        )
        return self._parse_response(text)

    # ---- internal ----
    @staticmethod
    def _build_message_content(
        blueprint_image_path: str,
        line_views: FourViewImage,
        shaded_views: FourViewImage,
    ) -> list[dict]:
        content: list[dict] = []
        # Set 1: reference (元図面 1 枚)
        content.append({"type": "text", "text": "## reference (original 2D drawing)"})
        content.append(image_file_block(blueprint_image_path))
        # Set 2: candidate (4 line + 4 shaded)
        content.append({"type": "text", "text": "## candidate — line drawings (top, front, side, iso)"})
        for png in line_views.as_list():
            content.append(png_bytes_block(png))
        content.append({"type": "text", "text": "## candidate — shaded renderings (top, front, side, iso)"})
        for png in shaded_views.as_list():
            content.append(png_bytes_block(png))
        # 指示文を最後に
        content.append({"type": "text", "text": P4_USER_TEXT})
        return content

    # ---- response parsing ----
    @staticmethod
    def _extract_json(text: str) -> str:
        """応答から JSON 部分を抽出"""
        m = re.search(r"```(?:json)?\s*\n(.*?)```", text, re.DOTALL)
        if m:
            return m.group(1).strip()
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return text[start : end + 1]
        return text.strip()

    @classmethod
    def _parse_response(cls, text: str) -> VerificationResult:
        try:
            data: dict[str, Any] = json.loads(cls._extract_json(text))
        except json.JSONDecodeError as e:
            logger.warning(f"[verify] JSON parse failed: {e}; raw text head: {text[:200]}")
            # JSON が壊れていても生レスポンスを返してフォールバック
            return VerificationResult.failure(
                feedback="JSON parse failed: VLM 応答を構造化できませんでした",
                discrepancies=tuple(),
                raw_response=text,
            )

        raw_list = data.get("discrepancies", []) or []
        discrepancies: list[Discrepancy] = []
        for raw in raw_list:
            if not isinstance(raw, dict):
                continue
            try:
                # location_hint / dimension_hint は null か空文字なら None として扱う
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
                logger.warning(f"[verify] skip malformed discrepancy: {raw} ({e})")
                continue

        critical_count = sum(1 for d in discrepancies if d.severity == "critical")
        is_valid = critical_count == 0
        feedback = "\n".join(d.to_feedback_line() for d in discrepancies) or None

        # is_valid に関わらず、検出された全 Discrepancy を返す
        # （major/minor も後段でレポート / 表示するため）
        return VerificationResult(
            is_valid=is_valid,
            discrepancies=tuple(discrepancies),
            feedback=feedback,
            raw_response=text,
        )
