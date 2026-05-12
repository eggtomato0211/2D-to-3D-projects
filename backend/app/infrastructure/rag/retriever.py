"""クエリ → 関連 chunk 上位 K 件を返す検索器。"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from .chunker import Chunk
from .embedder import OpenAIEmbedder
from .index import load_index


class CadQueryDocsRetriever:
    """事前構築された embedding index に対してクエリベース検索を行う。"""

    def __init__(self, index_dir: Path, embedder: OpenAIEmbedder | None = None):
        self.chunks, self.embeddings = load_index(index_dir)
        self.embedder = embedder or OpenAIEmbedder()

    def retrieve(self, query: str, top_k: int = 5,
                 score_threshold: float = 0.30) -> list[tuple[Chunk, float]]:
        """クエリに最も関連する chunk と類似度（コサイン）のペアを返す。"""
        q_vec = np.array(self.embedder.embed_one(query), dtype=np.float32)
        norm = np.linalg.norm(q_vec)
        if norm > 1e-9:
            q_vec = q_vec / norm
        # コサイン類似度 = ドット積（index 側で L2 正規化済み）
        sims = self.embeddings @ q_vec
        idx_sorted = np.argsort(-sims)
        out: list[tuple[Chunk, float]] = []
        for i in idx_sorted[:top_k * 3]:  # 多めに取って閾値フィルタ
            score = float(sims[i])
            if score < score_threshold:
                continue
            out.append((self.chunks[i], score))
            if len(out) >= top_k:
                break
        return out

    def retrieve_text(self, query: str, top_k: int = 5,
                      max_chars: int = 3000) -> str:
        """検索結果を 1 個の Markdown 文字列に組み立てる（system prompt への注入用）。"""
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
