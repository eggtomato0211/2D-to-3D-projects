from google import genai
from google.genai import types
from app.infrastructure.vlm.base.base_script_generator import BaseScriptGenerator


class GeminiScriptGenerator(BaseScriptGenerator):
    """
    Google Gemini を使用して CadQuery スクリプトを生成する。
    """

    def __init__(self, api_key: str, model: str = "gemini-2.5-pro"):
        self.client = genai.Client(api_key=api_key)
        self.model = model

    def _call_api(self, prompt: str) -> str:
        response = self.client.models.generate_content(
            model=self.model,
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=self._build_system_prompt()),
                        types.Part.from_text(text=prompt),
                    ],
                )
            ],
        )
        return response.text
