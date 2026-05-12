"""Reference Code RAG の retriever（ID blacklist 付き）。

評価時にデータリークを防ぐため、`exclude_ids` で test サンプル ID を
明示的に除外する。retrieve 結果に exclude ID が混ざっていれば AssertionError。
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np

from .embedder import OpenAIEmbedder

_log = logging.getLogger(__name__)


class ReferenceCodeRetriever:
    def __init__(self, index_dir: Path, embedder: OpenAIEmbedder | None = None,
                 exclude_ids: set[str] | None = None):
        data = np.load(index_dir / "embeddings.npz")
        self.embeddings: np.ndarray = data["embeddings"].astype(np.float32)
        self.entries: list[dict] = json.loads(
            (index_dir / "entries.json").read_text(encoding="utf-8")
        )
        self.embedder = embedder or OpenAIEmbedder()
        self.exclude_ids: set[str] = set(exclude_ids or set())

    def set_exclude_ids(self, ids: set[str]) -> None:
        """評価サンプル ID を後から差し替え可能にする。"""
        self.exclude_ids = set(ids)

    def retrieve(self, query: str, top_k: int = 3,
                 score_threshold: float = 0.40) -> list[tuple[dict, float]]:
        """query を embed → cosine similarity → top-K（exclude_ids を除外）。

        Hard assert: 返り値の ID が exclude_ids に含まれていたら例外。
        """
        q_vec = np.array(self.embedder.embed_one(query), dtype=np.float32)
        norm = np.linalg.norm(q_vec)
        if norm > 1e-9:
            q_vec = q_vec / norm
        sims = self.embeddings @ q_vec
        idx_sorted = np.argsort(-sims)
        out: list[tuple[dict, float]] = []
        for i in idx_sorted[: top_k * 5 + 5]:  # 多めに取って exclude フィルタ
            entry = self.entries[i]
            eid = str(entry.get("id", ""))
            if eid in self.exclude_ids:
                continue
            score = float(sims[i])
            if score < score_threshold:
                continue
            out.append((entry, score))
            if len(out) >= top_k:
                break
        # hard assert: 取得した中に exclude が混じってないか最終チェック
        for ent, _ in out:
            assert str(ent.get("id", "")) not in self.exclude_ids, (
                f"ID leak detected: {ent.get('id')}"
            )
        return out

    def retrieve_text(self, query: str, top_k: int = 3,
                      max_chars: int = 4000) -> str:
        """system context に注入するため markdown 文字列に整形。"""
        results = self.retrieve(query, top_k=top_k)
        if not results:
            return ""
        lines: list[str] = ["### 類似 GT 部品の操作列（参照のみ。改変して使用）"]
        total = 0
        for entry, score in results:
            block = (
                f"\n**[similarity {score:.2f}]** "
                f"id={entry.get('id')} ({entry.get('natural_summary', '?')})\n"
                f"特徴: bbox={entry.get('bbox')}, features={entry.get('features')}\n"
                f"```\n{entry.get('pseudo_code', '')}\n```\n"
            )
            if total + len(block) > max_chars:
                break
            lines.append(block)
            total += len(block)
        return "\n".join(lines)
