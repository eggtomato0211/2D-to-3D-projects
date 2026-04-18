from anthropic import Anthropic
from app.infrastructure.vlm.base.base_blueprint_analyzer import BaseBlueprintAnalyzer


class AnthropicBlueprintAnalyzer(BaseBlueprintAnalyzer):
    """
    Anthropic Claude を使用して図面を解析する。
    """

    def __init__(self, api_key: str, model: str = "claude-opus-4-7"):
        self.client = Anthropic(api_key=api_key)
        self.model = model

    def _call_api(self, image_data: str, mime_type: str) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=self._build_system_prompt(),
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": mime_type,
                                "data": image_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": "この図面のモデリング手順をJSON形式で出力してください。",
                        },
                    ],
                }
            ],
        )
        return response.content[0].text
