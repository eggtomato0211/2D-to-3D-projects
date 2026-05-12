"""Anthropic Messages API 用の image content block ヘルパ。

Verifier と Corrector の両方が使うため共有モジュールに切り出している。
"""
from __future__ import annotations

import base64
from pathlib import Path

_MIME_BY_SUFFIX = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
}


def _mime_for(path: str) -> str:
    return _MIME_BY_SUFFIX.get(Path(path).suffix.lower(), "image/png")


def png_bytes_block(png_bytes: bytes) -> dict:
    """PNG バイト列を Anthropic image block にする。"""
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": "image/png",
            "data": base64.b64encode(png_bytes).decode("ascii"),
        },
    }


def image_file_block(path: str) -> dict:
    """画像ファイルパスを Anthropic image block にする。"""
    data = Path(path).read_bytes()
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": _mime_for(path),
            "data": base64.b64encode(data).decode("ascii"),
        },
    }
