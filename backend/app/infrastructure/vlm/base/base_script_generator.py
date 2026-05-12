"""IScriptGenerator の共通ベースクラス。

各 VLM 実装が共有するロジック:
- generate / fix_script / correct_script / modify_parameters の組み立て
- RAG retriever（CadQuery docs + Reference Code）の DI と注入
- 応答テキストから ```python``` ブロックを抽出して CadScript にする

API 固有の呼び出し（_call_api）と、画像対応の correct_script は subclass で実装する。
"""
from __future__ import annotations

import re
from abc import abstractmethod
from typing import Optional

from app.domain.interfaces.cadquery_docs_retriever import ICadQueryDocsRetriever
from app.domain.interfaces.reference_code_retriever import IReferenceCodeRetriever
from app.domain.interfaces.script_generator import IScriptGenerator
from app.domain.value_objects.cad_script import CadScript
from app.domain.value_objects.clarification import Clarification
from app.domain.value_objects.design_step import DesignStep
from app.domain.value_objects.discrepancy import Discrepancy
from app.domain.value_objects.four_view_image import FourViewImage
from app.domain.value_objects.iteration_attempt import IterationAttempt
from app.domain.value_objects.model_parameter import ModelParameter

from . import _prompts
from .system_prompt import SYSTEM_PROMPT

_CODE_BLOCK_RE = re.compile(r"```python\s*\n(.*?)```", re.DOTALL)


class BaseScriptGenerator(IScriptGenerator):

    def __init__(
        self,
        docs_retriever: Optional[ICadQueryDocsRetriever] = None,
        ref_retriever: Optional[IReferenceCodeRetriever] = None,
    ) -> None:
        self._docs_retriever = docs_retriever
        self._ref_retriever = ref_retriever

    # ---- IScriptGenerator ----
    def generate(
        self,
        steps: list[DesignStep],
        clarifications: list[Clarification],
    ) -> CadScript:
        docs_block, ref_block = self._build_rag_blocks(steps)
        prompt = _prompts.build_intent_prompt(
            steps, clarifications,
            docs_block=docs_block, reference_block=ref_block,
        )
        return self._parse_response(self._call_api(prompt))

    def fix_script(self, script: CadScript, feedback: str) -> CadScript:
        prompt = _prompts.build_fix_prompt(script, feedback)
        return self._parse_response(self._call_api(prompt))

    def modify_parameters(
        self,
        script: CadScript,
        old_parameters: list[ModelParameter],
        new_parameters: list[ModelParameter],
    ) -> CadScript:
        prompt = _prompts.build_modify_parameters_prompt(
            script, old_parameters, new_parameters
        )
        return self._parse_response(self._call_api(prompt))

    def correct_script(
        self,
        script: CadScript,
        discrepancies: tuple[Discrepancy, ...],
        blueprint_image_path: Optional[str] = None,
        line_views: Optional[FourViewImage] = None,
        shaded_views: Optional[FourViewImage] = None,
        iteration_history: Optional[tuple[IterationAttempt, ...]] = None,
    ) -> CadScript:
        """テキストのみのフォールバック実装。

        Vision 対応の実装は subclass で override し、画像を入力に乗せた上で
        super().correct_script() ではなく自前の API 呼び出しを行うこと。
        """
        del blueprint_image_path, line_views, shaded_views
        prompt = _prompts.build_correct_prompt(
            script, discrepancies, iteration_history
        )
        return self._parse_response(self._call_api(prompt))

    # ---- helpers ----
    def _build_rag_blocks(self, steps: list[DesignStep]) -> tuple[str, str]:
        """設計手順をクエリにして両 RAG から抜粋を取得。例外時は空文字を返す。"""
        if not steps:
            return "", ""

        joined = "\n".join(step.instruction[:200] for step in steps[:6])
        docs_block = ""
        if self._docs_retriever is not None:
            try:
                docs_block = self._docs_retriever.retrieve_text(
                    joined, top_k=5, max_chars=2500
                )
            except Exception:
                docs_block = ""

        ref_block = ""
        if self._ref_retriever is not None:
            # 構造化参照ブロックがあればそれをクエリに優先（GT 検索に効く）
            ref_query = next(
                (s.instruction for s in steps if s.instruction.startswith("**【参照情報")),
                joined,
            )
            try:
                ref_block = self._ref_retriever.retrieve_text(
                    ref_query, top_k=3, max_chars=4000
                )
            except Exception:
                ref_block = ""

        return docs_block, ref_block

    def _build_system_prompt(self) -> str:
        return SYSTEM_PROMPT

    def _parse_response(self, content: str) -> CadScript:
        match = _CODE_BLOCK_RE.search(content)
        code = match.group(1).strip() if match else content.strip()
        return CadScript(content=code)

    # ---- subclass extension point ----
    @abstractmethod
    def _call_api(self, prompt: str) -> str:
        """system prompt + 与えられた user prompt で LLM を呼び出し、応答テキストを返す。"""
        ...
