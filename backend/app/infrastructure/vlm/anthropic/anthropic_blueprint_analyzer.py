"""Anthropic Claude を使った Blueprint Analyzer。"""
from __future__ import annotations

from anthropic import Anthropic

from app.infrastructure.vlm.base.base_blueprint_analyzer import BaseBlueprintAnalyzer

DEFAULT_MODEL = "claude-opus-4-7"
ANALYZE_MAX_TOKENS = 16384  # 構造化抽出を含む応答に余裕を持たせる
CROSS_CHECK_MAX_TOKENS = 4096


class AnthropicBlueprintAnalyzer(BaseBlueprintAnalyzer):

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL) -> None:
        self._client = Anthropic(api_key=api_key)
        self._model = model

    def _call_api(self, image_data: str, mime: str) -> str:
        resp = self._client.messages.create(
            model=self._model,
            max_tokens=ANALYZE_MAX_TOKENS,
            system=self._build_system_prompt(),
            messages=[{
                "role": "user",
                "content": [
                    self._image_block(image_data, mime),
                    {"type": "text", "text": "この図面のモデリング手順を JSON 形式で出力してください。"},
                ],
            }],
        )
        return resp.content[0].text

    def _call_cross_check(
        self, image_data: str, mime: str,
        system_prompt: str, user_text: str,
    ) -> str:
        resp = self._client.messages.create(
            model=self._model,
            max_tokens=CROSS_CHECK_MAX_TOKENS,
            system=system_prompt,
            messages=[{
                "role": "user",
                "content": [
                    self._image_block(image_data, mime),
                    {"type": "text", "text": user_text},
                ],
            }],
        )
        return resp.content[0].text if resp.content else ""

    @staticmethod
    def _image_block(image_data: str, mime: str) -> dict:
        return {
            "type": "image",
            "source": {"type": "base64", "media_type": mime, "data": image_data},
        }
