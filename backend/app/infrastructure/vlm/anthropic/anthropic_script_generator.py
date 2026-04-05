from anthropic import Anthropic
from app.infrastructure.vlm.base.base_script_generator import BaseScriptGenerator


class AnthropicScriptGenerator(BaseScriptGenerator):
    """
    Anthropic Claude を使用して CadQuery スクリプトを生成する。
    """

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self.client = Anthropic(api_key=api_key)
        self.model = model

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
