"""Anthropic Messages API 用の image content block ヘルパ。

Verifier と Corrector の両方が使うため共有モジュールに切り出している。
"""
from __future__ import annotations

import base64
from pathlib import Path


def _mime_for(path: str) -> str:
    suffix = Path(path).suffix.lower()
    return {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }.get(suffix, "image/png")


def png_bytes_block(png_bytes: bytes) -> dict:
    """PNG バイト列を Anthropic image block にする"""
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": "image/png",
            "data": base64.b64encode(png_bytes).decode("ascii"),
        },
    }


def image_file_block(path: str) -> dict:
    """ファイルパスから Anthropic image block を作る"""
    with open(path, "rb") as f:
        data = f.read()
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": _mime_for(path),
            "data": base64.b64encode(data).decode("ascii"),
        },
    }
