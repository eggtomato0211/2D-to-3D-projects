"""OpenAI Chat Completions API を使った CadQuery スクリプト生成器。

gpt-5 系は reasoning_effort="low" を指定して出力予算を確保する。
correct_script は基底のテキスト専用実装を使う（画像対応未実装）。
"""
from __future__ import annotations

from typing import Optional

from openai import OpenAI

from app.domain.interfaces.cadquery_docs_retriever import ICadQueryDocsRetriever
from app.domain.interfaces.reference_code_retriever import IReferenceCodeRetriever
from app.infrastructure.vlm.base.base_script_generator import BaseScriptGenerator

from ._retry import SDK_MAX_RETRIES, SDK_TIMEOUT, call_with_retry

DEFAULT_MODEL = "gpt-4o"
MAX_TOKENS = 16384


class OpenAIScriptGenerator(BaseScriptGenerator):

    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        max_tokens: int = MAX_TOKENS,
        docs_retriever: Optional[ICadQueryDocsRetriever] = None,
        ref_retriever: Optional[IReferenceCodeRetriever] = None,
    ) -> None:
        super().__init__(docs_retriever=docs_retriever, ref_retriever=ref_retriever)
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

    def _call_api(self, prompt: str) -> str:
        kwargs: dict = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": self._build_system_prompt()},
                {"role": "user", "content": prompt},
            ],
        }
        if self._is_reasoning_model():
            kwargs["reasoning_effort"] = "low"

        def _call():
            try:
                return self._client.chat.completions.create(
                    **kwargs, max_completion_tokens=self._max_tokens,
                )
            except TypeError:
                kwargs.pop("reasoning_effort", None)
                return self._client.chat.completions.create(
                    **kwargs, max_tokens=self._max_tokens,
                )

        resp = call_with_retry(_call)
        return resp.choices[0].message.content or ""
