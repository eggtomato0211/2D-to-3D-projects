"""cadquery_docs/*.md を chunk → embed → index に保存する。

実行: docker compose run --rm backend python -m app.infrastructure.rag.scripts.build_index
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

from app.infrastructure.rag.chunker import chunk_directory
from app.infrastructure.rag.embedder import OpenAIEmbedder
from app.infrastructure.rag.index import save_index

DOCS_DIR = Path("/app/app/infrastructure/rag/cadquery_docs")
INDEX_DIR = Path("/app/app/infrastructure/rag/cadquery_index")


def main() -> int:
    print(f"=== chunking {DOCS_DIR} ===")
    chunks = chunk_directory(DOCS_DIR)
    total_chars = sum(len(c.text) for c in chunks)
    print(f"  → {len(chunks)} chunks, total {total_chars} chars\n")

    print(f"=== embedding (model = text-embedding-3-small) ===")
    embedder = OpenAIEmbedder()
    t0 = time.time()
    vectors = embedder.embed([c.text for c in chunks])
    elapsed = time.time() - t0
    print(f"  → {len(vectors)} vectors in {elapsed:.1f}s\n")

    print(f"=== saving index to {INDEX_DIR} ===")
    save_index(INDEX_DIR, chunks, vectors)
    print(f"  ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
