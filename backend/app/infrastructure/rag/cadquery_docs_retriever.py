"""CadQuery 公式ドキュメント抜粋を返す検索器。"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from app.domain.interfaces.cadquery_docs_retriever import ICadQueryDocsRetriever

from .chunker import Chunk
from .embedder import OpenAIEmbedder
from .index import load_index


class CadQueryDocsRetriever(ICadQueryDocsRetriever):
    """事前構築済み embedding index に対してクエリベース検索を行う。"""

    def __init__(self, index_dir: Path, embedder: OpenAIEmbedder | None = None):
        self.chunks, self.embeddings = load_index(index_dir)
        self.embedder = embedder or OpenAIEmbedder()

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.30,
    ) -> list[tuple[Chunk, float]]:
        q_vec = np.array(self.embedder.embed_one(query), dtype=np.float32)
        norm = np.linalg.norm(q_vec)
        if norm > 1e-9:
            q_vec = q_vec / norm
        sims = self.embeddings @ q_vec
        idx_sorted = np.argsort(-sims)
        out: list[tuple[Chunk, float]] = []
        for i in idx_sorted[: top_k * 3]:
            score = float(sims[i])
            if score < score_threshold:
                continue
            out.append((self.chunks[i], score))
            if len(out) >= top_k:
                break
        return out

    def retrieve_text(self, query: str, top_k: int = 5, max_chars: int = 2500) -> str:
        results = self.retrieve(query, top_k=top_k)
        if not results:
            return ""
        lines: list[str] = ["### CadQuery 公式ドキュメントからの抜粋"]
        total = 0
        for chunk, score in results:
            block = (
                f"\n**[{chunk.source} / {chunk.section}]** (相関 {score:.2f})\n"
                f"{chunk.text}\n"
            )
            if total + len(block) > max_chars:
                break
            lines.append(block)
            total += len(block)
        return "\n".join(lines)
