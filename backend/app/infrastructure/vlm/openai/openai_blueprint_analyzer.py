"""OpenAI Chat Completions API を使った Blueprint Analyzer。"""
from __future__ import annotations

from openai import OpenAI

from app.infrastructure.vlm.base.base_blueprint_analyzer import BaseBlueprintAnalyzer

from ._retry import SDK_MAX_RETRIES, SDK_TIMEOUT, call_with_retry

DEFAULT_MODEL = "gpt-4o"
ANALYZE_MAX_TOKENS = 16384
CROSS_CHECK_MAX_TOKENS = 4096


class OpenAIBlueprintAnalyzer(BaseBlueprintAnalyzer):

    def __init__(
        self, api_key: str, model: str = DEFAULT_MODEL,
        max_tokens: int = ANALYZE_MAX_TOKENS,
    ) -> None:
        self._client = OpenAI(
            api_key=api_key,
            max_retries=SDK_MAX_RETRIES,
            timeout=SDK_TIMEOUT,
        )
        self._model = model
        self._max_tokens = max_tokens

    def _is_reasoning_model(self) -> bool:
        m = self._model.lower()
        return m.startswith("gpt-5") or m.startswith("o3") or m.startswith("o4")

    def _call_api(self, image_data: str, mime: str) -> str:
        return self._chat_completion(
            user_text="この図面のモデリング手順を出力してください。",
            image_data=image_data, mime=mime,
            system_prompt=self._build_system_prompt(),
            max_tokens=self._max_tokens,
        )

    def _call_cross_check(
        self, image_data: str, mime: str,
        system_prompt: str, user_text: str,
    ) -> str:
        return self._chat_completion(
            user_text=user_text, image_data=image_data, mime=mime,
            system_prompt=system_prompt,
            max_tokens=CROSS_CHECK_MAX_TOKENS,
        )

    def _chat_completion(
        self, user_text: str, image_data: str, mime: str,
        system_prompt: str, max_tokens: int,
    ) -> str:
        kwargs: dict = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_text},
                        {"type": "image_url",
                         "image_url": {"url": f"data:{mime};base64,{image_data}"}},
                    ],
                },
            ],
            "response_format": {"type": "json_object"},
        }
        if self._is_reasoning_model():
            kwargs["reasoning_effort"] = "low"

        def _call():
            try:
                return self._client.chat.completions.create(
                    **kwargs, max_completion_tokens=max_tokens,
                )
            except TypeError:
                kwargs.pop("reasoning_effort", None)
                return self._client.chat.completions.create(
                    **kwargs, max_tokens=max_tokens,
                )

        resp = call_with_retry(_call)
        return resp.choices[0].message.content or ""
