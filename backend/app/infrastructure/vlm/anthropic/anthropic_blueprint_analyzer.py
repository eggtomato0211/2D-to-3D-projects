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
        # 構造化抽出（dimensions_table / feature_inventory）を含む応答に余裕を持たせる
        response = self.client.messages.create(
            model=self.model,
            max_tokens=16384,
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

    def _call_cross_check(
        self, image_data: str, mime_type: str,
        system_prompt: str, user_text: str,
    ) -> str:
        """cross-check 用の追加 API 呼び出し（Anthropic）。"""
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system_prompt,
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
                        {"type": "text", "text": user_text},
                    ],
                }
            ],
        )
        return resp.content[0].text if resp.content else ""
