from typing import Optional

from anthropic import Anthropic
from loguru import logger

from app.domain.value_objects.cad_script import CadScript
from app.domain.value_objects.discrepancy import Discrepancy
from app.domain.value_objects.four_view_image import FourViewImage
from app.domain.value_objects.iteration_attempt import IterationAttempt
from app.infrastructure.vlm.anthropic._image_blocks import (
    image_file_block,
    png_bytes_block,
)
from app.infrastructure.vlm.base.base_script_generator import BaseScriptGenerator


class AnthropicScriptGenerator(BaseScriptGenerator):
    """
    Anthropic Claude を使用して CadQuery スクリプトを生成する。

    Phase 2-δ §10.1: correct_script は画像入力（元 2D 図面 + 4 視点レンダ）を
    受け取った場合、Vision API 経由で渡して視覚的修正を可能にする。
    """

    def __init__(self, api_key: str, model: str = "claude-opus-4-7",
                 docs_retriever=None, ref_retriever=None):
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self._docs_retriever = docs_retriever
        self._ref_retriever = ref_retriever

    def _call_api(self, prompt: str) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=self._build_system_prompt(),
            messages=[
                {"role": "user", "content": prompt},
            ],
        )
        return response.content[0].text

    # ------------------------------------------------------------------
    # Phase 2-δ §10.1: 画像入力対応版 correct_script
    # ------------------------------------------------------------------
    def correct_script(
        self,
        script: CadScript,
        discrepancies: tuple[Discrepancy, ...],
        blueprint_image_path: Optional[str] = None,
        line_views: Optional[FourViewImage] = None,
        shaded_views: Optional[FourViewImage] = None,
        iteration_history: Optional[tuple[IterationAttempt, ...]] = None,
    ) -> CadScript:
        # 画像が一切無ければテキストのみの基底実装にフォールバック
        if (
            blueprint_image_path is None
            and line_views is None
            and shaded_views is None
        ):
            return super().correct_script(
                script,
                discrepancies,
                blueprint_image_path,
                line_views,
                shaded_views,
                iteration_history,
            )

        text_prompt = self._build_correct_prompt(
            script, discrepancies, iteration_history,
        )
        content: list[dict] = []

        # 元 2D 図面
        if blueprint_image_path is not None:
            content.append({
                "type": "text",
                "text": "## reference (original 2D drawing)",
            })
            content.append(image_file_block(blueprint_image_path))

        # candidate 線画 4 視点
        if line_views is not None:
            content.append({
                "type": "text",
                "text": "## candidate — line drawings (top, front, side, iso)",
            })
            for png in line_views.as_list():
                content.append(png_bytes_block(png))

        # candidate 影付き 4 視点
        if shaded_views is not None:
            content.append({
                "type": "text",
                "text": "## candidate — shaded renderings (top, front, side, iso)",
            })
            for png in shaded_views.as_list():
                content.append(png_bytes_block(png))

        # text 指示は最後（画像との対応関係を見た上で読ませる）
        content.append({"type": "text", "text": text_prompt})

        msg = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=self._build_system_prompt(),
            messages=[{"role": "user", "content": content}],
        )
        text = "".join(b.text for b in msg.content if hasattr(b, "text"))
        logger.info(
            f"[correct_script] model={self.model} "
            f"in={msg.usage.input_tokens} out={msg.usage.output_tokens} "
            f"images=(bp={blueprint_image_path is not None} "
            f"line={line_views is not None} shaded={shaded_views is not None})"
        )
        return self._parse_response(text)
