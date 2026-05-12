"""Markdown 風テキストを意味単位の chunk に分割する。

戦略: ヘッダー（# / ## / ###）で大きく分け、それでも長いものは更に
~600 文字単位で分割。chunk 間に隣接の文脈を 100 文字程度オーバーラップ。
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Chunk:
    """1 個の検索単位。"""
    source: str          # ファイル名（例: "workplane.md"）
    section: str         # 該当セクション（先頭ヘッダー）
    text: str            # 本文
    chunk_id: str        # 一意 ID（{source}#{idx}）


_HEADER_RE = re.compile(r"^(#{1,4})\s+(.+)$", re.MULTILINE)


def _split_by_headers(text: str) -> list[tuple[str, str]]:
    """テキストをヘッダー境界で分割。

    返り値: (section_title, body) のリスト。
    """
    chunks: list[tuple[str, str]] = []
    matches = list(_HEADER_RE.finditer(text))
    if not matches:
        return [("(no header)", text)]
    # 最初のヘッダー前のテキストも保持
    if matches[0].start() > 0:
        prefix = text[: matches[0].start()].strip()
        if prefix:
            chunks.append(("(intro)", prefix))
    for i, m in enumerate(matches):
        title = m.group(2).strip()
        body_start = m.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[body_start:body_end].strip()
        if body:
            chunks.append((title, body))
    return chunks


def _split_long(text: str, max_chars: int = 1200, overlap: int = 150) -> list[str]:
    """長過ぎる本文を更に max_chars 程度の窓に分割（境界は段落優先）。"""
    if len(text) <= max_chars:
        return [text]
    pieces: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        if end < len(text):
            # 直近の段落境界（\n\n）を探す
            soft = text.rfind("\n\n", start, end)
            if soft > start + max_chars // 2:
                end = soft
            else:
                # 文末記号でも妥協
                soft = max(text.rfind("。", start, end), text.rfind(".\n", start, end))
                if soft > start + max_chars // 2:
                    end = soft + 1
        pieces.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(0, end - overlap)
    return [p for p in pieces if p]


def chunk_file(path: Path, max_chars: int = 1200, overlap: int = 150) -> list[Chunk]:
    """1 ファイルから Chunk のリストを返す。"""
    source = path.name
    raw = path.read_text(encoding="utf-8")
    out: list[Chunk] = []
    for section, body in _split_by_headers(raw):
        pieces = _split_long(body, max_chars=max_chars, overlap=overlap)
        for i, piece in enumerate(pieces):
            cid = f"{source}#{len(out)}"
            out.append(Chunk(
                source=source,
                section=section,
                text=f"## {section}\n\n{piece}" if section != "(intro)" else piece,
                chunk_id=cid,
            ))
    return out


def chunk_directory(docs_dir: Path) -> list[Chunk]:
    """ディレクトリ配下の .md を全て chunking。"""
    all_chunks: list[Chunk] = []
    for md in sorted(docs_dir.glob("*.md")):
        all_chunks.extend(chunk_file(md))
    return all_chunks
