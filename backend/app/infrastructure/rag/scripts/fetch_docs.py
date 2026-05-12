"""cadquery-ja.readthedocs.io から主要ドキュメントを取得してテキスト化する。

実行: docker compose run --rm backend python -m app.infrastructure.rag.scripts.fetch_docs
"""
from __future__ import annotations

import re
import sys
import urllib.request
from pathlib import Path
from html.parser import HTMLParser

OUTDIR = Path("/app/app/infrastructure/rag/cadquery_docs")
BASE = "https://cadquery-ja.readthedocs.io/ja/latest/"

PAGES = [
    ("intro", "intro.html"),
    ("workplane", "workplane.html"),
    ("sketch", "sketch.html"),
    ("assembly", "assy.html"),
    ("selectors", "selectors.html"),
    ("examples", "examples.html"),
    ("classreference", "classreference.html"),
    ("apireference", "apireference.html"),
    ("primer", "primer.html"),
    ("cheat_sheet", "RoughCheatSheet.html"),
]


class _TextExtractor(HTMLParser):
    """HTML から本文を抽出。pre/code は保持、他はテキスト化。"""

    SKIP_TAGS = {"script", "style", "nav", "footer", "header", "aside"}

    def __init__(self):
        super().__init__()
        self.parts: list[str] = []
        self._skip_depth = 0
        self._in_pre = False
        self._in_code = False
        self._in_main = False
        self._in_h = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP_TAGS:
            self._skip_depth += 1
            return
        attrs_d = dict(attrs)
        cls = attrs_d.get("class", "") or ""
        # main content をマーク
        if tag == "div" and ("body" in cls or "document" in cls or "rst-content" in cls):
            self._in_main = True
        if tag == "pre":
            self._in_pre = True
            self.parts.append("\n```python\n")
        elif tag == "code":
            self._in_code = True
            if not self._in_pre:
                self.parts.append("`")
        elif tag in ("h1", "h2", "h3", "h4"):
            self._in_h = int(tag[1])
            self.parts.append("\n" + "#" * self._in_h + " ")
        elif tag == "p":
            self.parts.append("\n\n")
        elif tag in ("li",):
            self.parts.append("\n- ")
        elif tag == "br":
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in self.SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
            return
        if tag == "pre":
            self._in_pre = False
            self.parts.append("\n```\n")
        elif tag == "code":
            self._in_code = False
            if not self._in_pre:
                self.parts.append("`")
        elif tag in ("h1", "h2", "h3", "h4"):
            self.parts.append("\n")
            self._in_h = 0

    def handle_data(self, data):
        if self._skip_depth > 0:
            return
        self.parts.append(data)

    def text(self) -> str:
        out = "".join(self.parts)
        # 連続空行を 2 行までに
        out = re.sub(r"\n{3,}", "\n\n", out)
        # 行頭スペースを軽くトリム
        out = "\n".join(line.rstrip() for line in out.splitlines())
        return out.strip()


def fetch(url: str) -> str:
    print(f"  fetching {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read().decode("utf-8", errors="replace")
    p = _TextExtractor()
    p.feed(raw)
    return p.text()


def main() -> int:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    print(f"=== fetching CadQuery docs to {OUTDIR} ===\n")
    for name, path in PAGES:
        url = BASE + path
        try:
            text = fetch(url)
        except Exception as e:
            print(f"  [!] {name}: {type(e).__name__}: {e}")
            continue
        out = OUTDIR / f"{name}.md"
        out.write_text(text, encoding="utf-8")
        print(f"  [OK] {name}: {len(text)} chars → {out.name}")
    print("\n[done]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
