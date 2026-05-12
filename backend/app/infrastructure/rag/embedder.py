"""OpenAI Embeddings の薄いラッパー。

`text-embedding-3-small` を既定（1536 dim、安価）。
"""
from __future__ import annotations

import os

from openai import OpenAI

DEFAULT_MODEL = "text-embedding-3-small"


class OpenAIEmbedder:
    def __init__(self, api_key: str | None = None, model: str = DEFAULT_MODEL):
        self.client = OpenAI(api_key=api_key or os.environ["OPENAI_API_KEY"])
        self.model = model

    def embed(self, texts: list[str], batch_size: int = 64) -> list[list[float]]:
        out: list[list[float]] = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            resp = self.client.embeddings.create(model=self.model, input=batch)
            out.extend(d.embedding for d in resp.data)
        return out

    def embed_one(self, text: str) -> list[float]:
        return self.embed([text])[0]
