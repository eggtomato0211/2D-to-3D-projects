from openai import OpenAI
from app.infrastructure.vlm.base.base_script_generator import BaseScriptGenerator
from app.infrastructure.vlm.openai._retry import (
    SDK_MAX_RETRIES, SDK_TIMEOUT, call_with_retry,
)


class OpenAIScriptGenerator(BaseScriptGenerator):
    """OpenAI Chat Completions API（GPT-4o / 4.1 / 5.x 系）で CadQuery を生成する。"""

    def __init__(self, api_key: str, model: str = "gpt-4o", max_tokens: int = 16384,
                 docs_retriever=None, ref_retriever=None):
        # SDK 内蔵のリトライを 5 回まで上げ、タイムアウトも長めに
        self.client = OpenAI(
            api_key=api_key,
            max_retries=SDK_MAX_RETRIES,
            timeout=SDK_TIMEOUT,
        )
        self.model = model
        self.max_tokens = max_tokens
        self._docs_retriever = docs_retriever
        self._ref_retriever = ref_retriever

    def _is_reasoning_model(self) -> bool:
        # gpt-5 系 / o3 / o4 系は reasoning tokens を消費するので予算大きく
        m = self.model.lower()
        return m.startswith("gpt-5") or m.startswith("o3") or m.startswith("o4")

    def _call_api(self, prompt: str) -> str:
        common_kwargs = dict(
            model=self.model,
            messages=[
                {"role": "system", "content": self._build_system_prompt()},
                {"role": "user", "content": prompt},
            ],
        )
        # reasoning_effort="low" で reasoning tokens 消費を抑制（出力可視部分への予算確保）
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
