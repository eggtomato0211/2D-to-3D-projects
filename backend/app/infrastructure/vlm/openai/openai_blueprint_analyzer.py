from openai import OpenAI
from app.infrastructure.vlm.base.base_blueprint_analyzer import BaseBlueprintAnalyzer
from app.infrastructure.vlm.openai._retry import (
    SDK_MAX_RETRIES, SDK_TIMEOUT, call_with_retry,
)


class OpenAIBlueprintAnalyzer(BaseBlueprintAnalyzer):
    """OpenAI Chat Completions API（GPT-4o / 4.1 / 5.x 系）で図面を解析する。"""

    def __init__(self, api_key: str, model: str = "gpt-4o", max_tokens: int = 16384):
        # SDK 内蔵リトライを増やし、タイムアウトも長めに
        self.client = OpenAI(
            api_key=api_key,
            max_retries=SDK_MAX_RETRIES,
            timeout=SDK_TIMEOUT,
        )
        self.model = model
        self.max_tokens = max_tokens

    def _is_reasoning_model(self) -> bool:
        m = self.model.lower()
        return m.startswith("gpt-5") or m.startswith("o3") or m.startswith("o4")

    def _call_api(self, image_data: str, mime_type: str) -> str:
        # GPT-5 系は max_completion_tokens、4o 系は max_tokens を使う
        common_kwargs = dict(
            model=self.model,
            messages=[
                {"role": "system", "content": self._build_system_prompt()},
                {
                    "role": "user",
                    "content": [
                        {"type": "text",
                         "text": "この図面のモデリング手順を出力してください。"},
                        {"type": "image_url",
                         "image_url": {"url": f"data:{mime_type};base64,{image_data}"}},
                    ],
                },
            ],
            response_format={"type": "json_object"},
        )
        if self._is_reasoning_model():
            common_kwargs["reasoning_effort"] = "low"

        def _do_call():
            try:
                return self.client.chat.completions.create(
                    **common_kwargs, max_completion_tokens=self.max_tokens,
                )
            except TypeError:
                common_kwargs.pop("reasoning_effort", None)
                return self.client.chat.completions.create(
                    **common_kwargs, max_tokens=self.max_tokens,
                )

        response = call_with_retry(_do_call)
        return response.choices[0].message.content or ""

    def _call_cross_check(
        self, image_data: str, mime_type: str,
        system_prompt: str, user_text: str,
    ) -> str:
        """cross-check 用の追加 API 呼び出し（OpenAI）。"""
        common_kwargs = dict(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_text},
                        {"type": "image_url",
                         "image_url": {"url": f"data:{mime_type};base64,{image_data}"}},
                    ],
                },
            ],
            response_format={"type": "json_object"},
        )
        if self._is_reasoning_model():
            common_kwargs["reasoning_effort"] = "low"

        def _do_call():
            try:
                return self.client.chat.completions.create(
                    **common_kwargs, max_completion_tokens=4096,
                )
            except TypeError:
                common_kwargs.pop("reasoning_effort", None)
                return self.client.chat.completions.create(
                    **common_kwargs, max_tokens=4096,
                )
        resp = call_with_retry(_do_call)
        return resp.choices[0].message.content or ""
