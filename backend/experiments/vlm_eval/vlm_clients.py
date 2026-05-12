"""VLM クライアント抽象化。Anthropic と OpenAI を同じ interface で扱う。"""
from __future__ import annotations

import base64
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass
class VlmResponse:
    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    duration_sec: float = 0.0
    error: str | None = None


def _encode_image(path: Path) -> tuple[str, str]:
    """画像を base64 エンコードして (data, mime) を返す"""
    with open(path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode("ascii"), "image/png"


class IVlmClient(ABC):
    name: str

    @abstractmethod
    def call(
        self,
        system: str,
        user_text: str,
        ref_images: list[Path],
        cand_images: list[Path],
    ) -> VlmResponse:
        ...


# ----------------------------------------------------------------------------
# Anthropic Claude
# ----------------------------------------------------------------------------
class AnthropicClient(IVlmClient):
    def __init__(self, model: str, name: str | None = None):
        from anthropic import Anthropic
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set")
        self._client = Anthropic(api_key=api_key)
        self.model = model
        self.name = name or f"anthropic/{model}"

    def call(self, system, user_text, ref_images, cand_images):
        started = time.time()
        try:
            content: list[dict] = []
            content.append({"type": "text", "text": "## reference 画像群"})
            for p in ref_images:
                data, mime = _encode_image(p)
                content.append({
                    "type": "image",
                    "source": {"type": "base64", "media_type": mime, "data": data},
                })
            content.append({"type": "text", "text": "## candidate 画像群"})
            for p in cand_images:
                data, mime = _encode_image(p)
                content.append({
                    "type": "image",
                    "source": {"type": "base64", "media_type": mime, "data": data},
                })
            content.append({"type": "text", "text": user_text})

            msg = self._client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=system,
                messages=[{"role": "user", "content": content}],
            )
            text = "".join(b.text for b in msg.content if hasattr(b, "text"))
            return VlmResponse(
                text=text,
                input_tokens=msg.usage.input_tokens,
                output_tokens=msg.usage.output_tokens,
                duration_sec=time.time() - started,
            )
        except Exception as e:
            return VlmResponse(
                text="", duration_sec=time.time() - started, error=f"{type(e).__name__}: {e}"
            )


# ----------------------------------------------------------------------------
# OpenAI
# ----------------------------------------------------------------------------
class OpenAIClient(IVlmClient):
    def __init__(self, model: str, name: str | None = None):
        from openai import OpenAI
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set")
        self._client = OpenAI(api_key=api_key)
        self.model = model
        self.name = name or f"openai/{model}"

    def call(self, system, user_text, ref_images, cand_images):
        started = time.time()
        try:
            content: list[dict] = []
            content.append({"type": "text", "text": "## reference 画像群"})
            for p in ref_images:
                data, mime = _encode_image(p)
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime};base64,{data}"},
                })
            content.append({"type": "text", "text": "## candidate 画像群"})
            for p in cand_images:
                data, mime = _encode_image(p)
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime};base64,{data}"},
                })
            content.append({"type": "text", "text": user_text})

            resp = self._client.chat.completions.create(
                model=self.model,
                max_tokens=2048,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": content},
                ],
            )
            text = resp.choices[0].message.content or ""
            usage = resp.usage
            return VlmResponse(
                text=text,
                input_tokens=usage.prompt_tokens if usage else 0,
                output_tokens=usage.completion_tokens if usage else 0,
                duration_sec=time.time() - started,
            )
        except Exception as e:
            return VlmResponse(
                text="", duration_sec=time.time() - started, error=f"{type(e).__name__}: {e}"
            )


# ----------------------------------------------------------------------------
# Default model set
# ----------------------------------------------------------------------------
def default_clients() -> list[IVlmClient]:
    """実験デフォルトのクライアント集合。実環境の API キー有無で取捨選択する"""
    clients: list[IVlmClient] = []
    if os.environ.get("ANTHROPIC_API_KEY"):
        # Sonnet は Case B の P4 比較ではコスト節約のため一時無効化
        # clients.append(AnthropicClient("claude-sonnet-4-5", name="claude-sonnet-4-5"))
        clients.append(AnthropicClient("claude-opus-4-7", name="claude-opus-4-7"))
    # GPT-4o は Stage 1/2 で線画を誤認・hallucinate する傾向が強かったため一時無効化。
    # 必要なら以下のコメントアウトを解除する。
    # if os.environ.get("OPENAI_API_KEY"):
    #     clients.append(OpenAIClient("gpt-4o", name="gpt-4o"))
    return clients
