"""chunk + embedding を保存・ロードする index ストレージ。

検索時は in-memory に numpy 行列をロードしてドット積で top-K。
"""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import numpy as np

from .chunker import Chunk

INDEX_NPZ = "embeddings.npz"
INDEX_META = "chunks.json"


def save_index(index_dir: Path, chunks: list[Chunk], vectors: list[list[float]]) -> None:
    index_dir.mkdir(parents=True, exist_ok=True)
    arr = np.array(vectors, dtype=np.float32)
    # L2 正規化（cosine 類似度をドット積で算出するため）
    norms = np.linalg.norm(arr, axis=1, keepdims=True)
    arr = arr / np.clip(norms, 1e-9, None)
    np.savez_compressed(index_dir / INDEX_NPZ, embeddings=arr)
    (index_dir / INDEX_META).write_text(
        json.dumps([asdict(c) for c in chunks], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_index(index_dir: Path) -> tuple[list[Chunk], np.ndarray]:
    data = np.load(index_dir / INDEX_NPZ)
    embeddings: np.ndarray = data["embeddings"].astype(np.float32)
    meta = json.loads((index_dir / INDEX_META).read_text(encoding="utf-8"))
    return [Chunk(**m) for m in meta], embeddings
