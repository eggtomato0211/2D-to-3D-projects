from google import genai
from google.genai import types
from app.infrastructure.vlm.base.base_blueprint_analyzer import BaseBlueprintAnalyzer


class GeminiBlueprintAnalyzer(BaseBlueprintAnalyzer):
    """
    Google Gemini を使用して図面を解析する。
    """

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self.client = genai.Client(api_key=api_key)
        self.model = model

    def _call_api(self, image_data: str) -> str:
        response = self.client.models.generate_content(
            model=self.model,
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(self._build_system_prompt()),
                        types.Part.from_bytes(
                            data=bytes.fromhex(
                                __import__("base64").b64decode(image_data).hex()
                            ),
                            mime_type="image/png",
                        ),
                        types.Part.from_text(
                            "この図面のモデリング手順を出力してください。"
                        ),
                    ],
                )
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        return response.text
