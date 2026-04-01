from app.domain.entities.design_intent import DesignIntent
from app.domain.value_objects.cad_script import CadScript
from app.domain.interfaces.script_generator import IScriptGenerator
from abc import abstractmethod
import re


class BaseScriptGenerator(IScriptGenerator):

    def generate(self, design_intent: DesignIntent) -> CadScript:
        prompt = self._build_intent_prompt(design_intent)
        content = self._call_api(prompt)
        return self._parse_response(content)

    def _build_intent_prompt(self, design_intent: DesignIntent) -> str:
        """DesignIntent の steps を LLM に渡すプロンプト文字列に変換する"""
        steps_text = "\n".join(
            f"{step.step_number}. {step.instruction}"
            for step in design_intent.steps
        )
        return f"以下の設計手順に基づいて、CadQuery スクリプトを生成してください:\n\n{steps_text}"

    def _build_system_prompt(self) -> str:
        """CadQuery コード生成用のシステムプロンプトを返す"""
        return """あなたは CadQuery の熟練エンジニアです。
与えられた設計手順に基づいて、CadQuery の Python スクリプトを生成してください。

ルール:
- import cadquery as cq から始めること
- 最終結果は result 変数に代入すること
- コードのみを出力し、説明文は不要
- コードは ```python ``` で囲むこと"""

    def _parse_response(self, content: str) -> CadScript:
        """LLM の応答から Python コードブロックを抽出して CadScript に変換する"""
        match = re.search(r"```python\s*\n(.*?)```", content, re.DOTALL)
        if match:
            code = match.group(1).strip()
        else:
            code = content.strip()
        return CadScript(content=code)

    @abstractmethod
    def _call_api(self, prompt: str) -> str:
        """LLM API を呼び出し、レスポンス文字列を返す"""
        pass
    


