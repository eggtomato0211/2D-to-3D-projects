from openai import OpenAI
from app.infrastructure.vlm.base.base_script_generator import BaseScriptGenerator


class OpenAIScriptGenerator(BaseScriptGenerator):
    """
    OpenAI GPT-4o を使用して CadQuery スクリプトを生成する。
    """

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def _call_api(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self._build_system_prompt()},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content
