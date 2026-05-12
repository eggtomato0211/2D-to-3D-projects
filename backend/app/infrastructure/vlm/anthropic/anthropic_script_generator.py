"""Anthropic Claude を使った CadQuery スクリプト生成器。

correct_script は Vision API を使い、元 2D 図面 + 候補の 4 視点画像を
画像入力として乗せた状態で修正を依頼する。
"""
from __future__ import annotations

from typing import Optional

from anthropic import Anthropic
from loguru import logger

from app.domain.interfaces.cadquery_docs_retriever import ICadQueryDocsRetriever
from app.domain.interfaces.reference_code_retriever import IReferenceCodeRetriever
from app.domain.value_objects.cad_script import CadScript
from app.domain.value_objects.discrepancy import Discrepancy
from app.domain.value_objects.four_view_image import FourViewImage
from app.domain.value_objects.iteration_attempt import IterationAttempt
from app.infrastructure.vlm.anthropic._image_blocks import (
    image_file_block,
    png_bytes_block,
)
from app.infrastructure.vlm.base import _prompts
from app.infrastructure.vlm.base.base_script_generator import BaseScriptGenerator

DEFAULT_MODEL = "claude-opus-4-7"
MAX_TOKENS = 4096


class AnthropicScriptGenerator(BaseScriptGenerator):

    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        docs_retriever: Optional[ICadQueryDocsRetriever] = None,
        ref_retriever: Optional[IReferenceCodeRetriever] = None,
    ) -> None:
        super().__init__(docs_retriever=docs_retriever, ref_retriever=ref_retriever)
        self._client = Anthropic(api_key=api_key)
        self._model = model

    def _call_api(self, prompt: str) -> str:
        msg = self._client.messages.create(
            model=self._model,
            max_tokens=MAX_TOKENS,
            system=self._build_system_prompt(),
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text

    def correct_script(
        self,
        script: CadScript,
        discrepancies: tuple[Discrepancy, ...],
        blueprint_image_path: Optional[str] = None,
        line_views: Optional[FourViewImage] = None,
        shaded_views: Optional[FourViewImage] = None,
        iteration_history: Optional[tuple[IterationAttempt, ...]] = None,
    ) -> CadScript:
        if blueprint_image_path is None and line_views is None and shaded_views is None:
            return super().correct_script(
                script, discrepancies,
                blueprint_image_path, line_views, shaded_views, iteration_history,
            )

        text_prompt = _prompts.build_correct_prompt(
            script, discrepancies, iteration_history
        )
        content: list[dict] = []

        if blueprint_image_path is not None:
            content.append({"type": "text", "text": "## reference (original 2D drawing)"})
            content.append(image_file_block(blueprint_image_path))
        if line_views is not None:
            content.append({
                "type": "text",
                "text": "## candidate — line drawings (top, front, side, iso)",
            })
            content.extend(png_bytes_block(p) for p in line_views.as_list())
        if shaded_views is not None:
            content.append({
                "type": "text",
                "text": "## candidate — shaded renderings (top, front, side, iso)",
            })
            content.extend(png_bytes_block(p) for p in shaded_views.as_list())
        content.append({"type": "text", "text": text_prompt})

        msg = self._client.messages.create(
            model=self._model,
            max_tokens=MAX_TOKENS,
            system=self._build_system_prompt(),
            messages=[{"role": "user", "content": content}],
        )
        text = "".join(b.text for b in msg.content if hasattr(b, "text"))
        logger.info(
            f"[correct] model={self._model} "
            f"in={msg.usage.input_tokens} out={msg.usage.output_tokens} "
            f"images=(bp={blueprint_image_path is not None} "
            f"line={line_views is not None} shaded={shaded_views is not None})"
        )
        return self._parse_response(text)
