"""DeepCAD 等から構築した Reference Code corpus を検索する retriever。

3 層リーク防止:
1. データ層: corpus は train split のみで構築済み
2. 検索層: exclude_ids で評価対象 ID を retrieve から除外
3. 検証層: 返り値に exclude_id が混入していたら hard assert
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from app.domain.interfaces.reference_code_retriever import IReferenceCodeRetriever

from .embedder import OpenAIEmbedder


class ReferenceCodeRetriever(IReferenceCodeRetriever):

    def __init__(
        self,
        index_dir: Path,
        embedder: OpenAIEmbedder | None = None,
        exclude_ids: set[str] | None = None,
    ) -> None:
        data = np.load(index_dir / "embeddings.npz")
        self.embeddings: np.ndarray = data["embeddings"].astype(np.float32)
        self.entries: list[dict] = json.loads(
            (index_dir / "entries.json").read_text(encoding="utf-8")
        )
        self.embedder = embedder or OpenAIEmbedder()
        self._exclude_ids: set[str] = set(exclude_ids or set())

    def set_exclude_ids(self, ids: set[str]) -> None:
        self._exclude_ids = set(ids)

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        score_threshold: float = 0.40,
    ) -> list[tuple[dict, float]]:
        q_vec = np.array(self.embedder.embed_one(query), dtype=np.float32)
        norm = np.linalg.norm(q_vec)
        if norm > 1e-9:
            q_vec = q_vec / norm
        sims = self.embeddings @ q_vec
        idx_sorted = np.argsort(-sims)

        out: list[tuple[dict, float]] = []
        for i in idx_sorted[: top_k * 5 + 5]:
            entry = self.entries[i]
            eid = str(entry.get("id", ""))
            if eid in self._exclude_ids:
                continue
            score = float(sims[i])
            if score < score_threshold:
                continue
            out.append((entry, score))
            if len(out) >= top_k:
                break

        for entry, _ in out:
            assert str(entry.get("id", "")) not in self._exclude_ids, (
                f"ID leak detected: {entry.get('id')}"
            )
        return out

    def retrieve_text(self, query: str, top_k: int = 3, max_chars: int = 4000) -> str:
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
