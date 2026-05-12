"""図面ファイル（PDF or PNG/JPG）を VLM 入力用に整形するヘルパー。

- PDF → 1 ページ目を PNG に変換
- 画像が 4MB 超なら段階的に縮小 + JPEG 変換
- 最終的に base64 + MIME を返す
"""
from __future__ import annotations

import base64
import io

from loguru import logger

MAX_IMAGE_BYTES = 4 * 1024 * 1024  # API 上限 5MB に余裕を持たせる


def pdf_first_page_to_png(file_path: str) -> bytes:
    """PDF の 1 ページ目を 300 dpi で PNG に変換する。"""
    from pdf2image import convert_from_path

    images = convert_from_path(file_path, first_page=1, last_page=1, dpi=300)
    buf = io.BytesIO()
    images[0].save(buf, format="PNG")
    return buf.getvalue()


def compress_if_needed(image_bytes: bytes, mime_type: str) -> tuple[bytes, str]:
    """4MB を超える画像を段階的に縮小 + JPEG 変換する。"""
    if len(image_bytes) <= MAX_IMAGE_BYTES:
        return image_bytes, mime_type

    from PIL import Image

    img = Image.open(io.BytesIO(image_bytes))
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    quality = 85
    scale = 1.0
    compressed = image_bytes
    for _ in range(5):
        buf = io.BytesIO()
        if scale < 1.0:
            resized = img.resize(
                (int(img.width * scale), int(img.height * scale)),
                Image.LANCZOS,
            )
        else:
            resized = img
        resized.save(buf, format="JPEG", quality=quality)
        compressed = buf.getvalue()
        if len(compressed) <= MAX_IMAGE_BYTES:
            logger.info(
                f"画像を圧縮: {len(image_bytes)} -> {len(compressed)} bytes "
                f"(scale={scale:.2f}, quality={quality})"
            )
            return compressed, "image/jpeg"
        scale *= 0.75
        quality = max(quality - 10, 50)

    logger.warning(f"圧縮後も {len(compressed)} bytes — そのまま送信します")
    return compressed, "image/jpeg"


def encode_image_for_vlm(file_path: str, content_type: str) -> tuple[str, str]:
    """画像 / PDF を読み込み、(base64 文字列, MIME) を返す。"""
    if content_type == "application/pdf":
        image_bytes = pdf_first_page_to_png(file_path)
    else:
        with open(file_path, "rb") as f:
            image_bytes = f.read()

    image_bytes, mime = compress_if_needed(image_bytes, content_type)
    return base64.b64encode(image_bytes).decode("utf-8"), mime
