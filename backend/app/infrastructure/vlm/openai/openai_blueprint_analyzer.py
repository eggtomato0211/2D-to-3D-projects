from openai import OpenAI
from app.infrastructure.vlm.base.base_blueprint_analyzer import BaseBlueprintAnalyzer


class OpenAIBlueprintAnalyzer(BaseBlueprintAnalyzer):
    """
    OpenAI GPT-4o を使用して図面を解析する。
    """

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def _call_api(self, image_data: str, mime_type: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self._build_system_prompt()},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "この図面のモデリング手順を出力してください。",
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_data}"
                            },
                        },
                    ],
                },
            ],
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content
