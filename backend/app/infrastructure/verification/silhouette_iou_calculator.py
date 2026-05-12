"""PIL + numpy による軽量シルエット IoU 計算。

外部依存は既に backend に入っている PIL と numpy のみ (OpenCV 不要)。

アルゴリズム:
  1. 元 2D 図面と候補各視点を grayscale → 二値化 (暗い画素 = foreground)
  2. dilate で線を少し太く (細線の位置ズレに耐える)
  3. foreground の bbox にクロップ → 同サイズに NEAREST リサイズで正規化
  4. ピクセル IoU を計算、top / front / side の最大値を返す

blueprint は複数視点 + 寸法線が混在するため絶対値の IoU は低めに出る。
誤判定を抑えるため、しきい値は十分小さく (例: 0.15) 取って「明らかに乖離」のみ拾う。
"""
from __future__ import annotations

import io
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter
from loguru import logger

from app.domain.interfaces.silhouette_iou_calculator import ISilhouetteIouCalculator
from app.domain.value_objects.four_view_image import FourViewImage

# ハイパーパラメータ (基本は config 経由ではなくモジュール定数で固定)
_BIN_THRESHOLD = 200          # 二値化のしきい値 (gray < これ → foreground)
_DILATE_RADIUS = 2            # 線の太め化半径
_NORMALIZE_SIZE = 256         # bbox クロップ後にリサイズする辺サイズ


def _to_mask(img: Image.Image) -> np.ndarray:
    """画像 → bool 2D 配列 (True = foreground / 線)。"""
    gray = np.asarray(img.convert("L"))
    mask = gray < _BIN_THRESHOLD
    if _DILATE_RADIUS > 0:
        bin_img = Image.fromarray((mask.astype(np.uint8)) * 255)
        bin_img = bin_img.filter(ImageFilter.MaxFilter(_DILATE_RADIUS * 2 + 1))
        mask = np.asarray(bin_img) > 127
    return mask


def _crop_bbox_and_resize(mask: np.ndarray, size: int) -> np.ndarray:
    """foreground の bbox にクロップしてから (size, size) にリサイズ。"""
    rows = np.where(mask.any(axis=1))[0]
    cols = np.where(mask.any(axis=0))[0]
    if rows.size == 0 or cols.size == 0:
        return np.zeros((size, size), dtype=bool)

    cropped = mask[rows[0]: rows[-1] + 1, cols[0]: cols[-1] + 1]
    img = Image.fromarray((cropped.astype(np.uint8)) * 255)
    img = img.resize((size, size), Image.NEAREST)
    return np.asarray(img) > 127


def _pair_iou(a: np.ndarray, b: np.ndarray) -> float:
    inter = int(np.logical_and(a, b).sum())
    union = int(np.logical_or(a, b).sum())
    return float(inter) / float(max(union, 1))


def _load_image_from_path(path: str) -> Image.Image:
    return Image.open(path)


def _load_image_from_bytes(data: bytes) -> Image.Image:
    return Image.open(io.BytesIO(data))


class SilhouetteIouCalculator(ISilhouetteIouCalculator):

    def compute(
        self, blueprint_image_path: str, candidate_views: FourViewImage
    ) -> float:
        try:
            bp_img = _load_image_from_path(blueprint_image_path)
        except Exception as e:
            logger.warning(f"[silhouette-iou] failed to load blueprint: {e}")
            return 1.0  # 計算不能 → benefit of doubt

        bp_mask = _crop_bbox_and_resize(_to_mask(bp_img), _NORMALIZE_SIZE)
        if not bp_mask.any():
            logger.warning("[silhouette-iou] blueprint silhouette is empty")
            return 1.0

        best_iou = 0.0
        best_view = ""
        for name, png in (
            ("top", candidate_views.top),
            ("front", candidate_views.front),
            ("side", candidate_views.side),
        ):
            try:
                cv_img = _load_image_from_bytes(png)
            except Exception as e:
                logger.warning(f"[silhouette-iou] failed to load {name}: {e}")
                continue
            cv_mask = _crop_bbox_and_resize(_to_mask(cv_img), _NORMALIZE_SIZE)
            iou = _pair_iou(bp_mask, cv_mask)
            if iou > best_iou:
                best_iou = iou
                best_view = name

        logger.info(
            f"[silhouette-iou] best={best_iou:.3f} (view={best_view or 'n/a'})"
        )
        return best_iou
