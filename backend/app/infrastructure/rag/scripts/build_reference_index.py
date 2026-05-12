"""reference_codes/*.json を embedding → reference_index/ に保存。

実行: docker compose run --rm backend python -m app.infrastructure.rag.scripts.build_reference_index
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

from app.infrastructure.rag.embedder import OpenAIEmbedder

CORPUS_DIR = Path("/app/app/infrastructure/rag/reference_codes")
INDEX_DIR = Path("/app/app/infrastructure/rag/reference_index")


def main() -> int:
    files = sorted(CORPUS_DIR.glob("*.json"))
    print(f"=== building reference_index from {len(files)} entries ===\n")
    entries: list[dict] = []
    queries: list[str] = []
    for f in files:
        try:
            d = json.loads(f.read_text())
            entries.append(d)
            queries.append(d.get("query_text", ""))
        except Exception as e:
            print(f"  skip {f.name}: {e}")
    print(f"  loaded {len(entries)} entries")

    embedder = OpenAIEmbedder()
    t0 = time.time()
    vectors = embedder.embed(queries)
    elapsed = time.time() - t0
    print(f"  embedded {len(vectors)} queries in {elapsed:.0f}s")

    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    arr = np.array(vectors, dtype=np.float32)
    norms = np.linalg.norm(arr, axis=1, keepdims=True)
    arr = arr / np.clip(norms, 1e-9, None)
    np.savez_compressed(INDEX_DIR / "embeddings.npz", embeddings=arr)
    # entries の最小限の情報を保存（pseudo_code 含む）
    (INDEX_DIR / "entries.json").write_text(
        json.dumps(entries, ensure_ascii=False), encoding="utf-8"
    )
    print(f"  saved to {INDEX_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
