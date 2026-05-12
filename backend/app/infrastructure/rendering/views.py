"""4 視点（top/front/side/iso）のカメラ規約。

JIS B 0001 第三角法に準拠:
- top:   +Z 方向に視点（平面図）
- front: -Y 方向に視点（正面図）
- side:  +X 方向に視点（右側面図）
- iso:   (+1, -1, +1) 方向の等角投影
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

IMAGE_SIZE = (1024, 1024)
BG_COLOR_RGB = (1.0, 1.0, 1.0)


@dataclass(frozen=True)
class ViewSpec:
    name: str
    eye_dir: tuple[float, float, float]   # 視点方向（単位ベクトル化される）
    up: tuple[float, float, float]
    is_orthographic: bool                  # True: 直交投影 / False: 透視投影


VIEWS: tuple[ViewSpec, ...] = (
    ViewSpec("top",   (0.0, 0.0, 1.0),  (0.0, 1.0, 0.0), True),
    ViewSpec("front", (0.0, -1.0, 0.0), (0.0, 0.0, 1.0), True),
    ViewSpec("side",  (1.0, 0.0, 0.0),  (0.0, 0.0, 1.0), True),
    ViewSpec("iso",   (1.0, -1.0, 1.0), (0.0, 0.0, 1.0), False),
)


def _normalize(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v)
    return v if n < 1e-12 else v / n


def camera_pose_for_view(
    view: ViewSpec,
    bbox_center: np.ndarray,
    bbox_diag: float,
) -> tuple[np.ndarray, float]:
    """OpenGL/pyrender 互換の camera-to-world transform を返す。"""
    direction = _normalize(np.array(view.eye_dir, dtype=float))
    distance = bbox_diag * 1.6
    eye = bbox_center + direction * distance

    forward = _normalize(bbox_center - eye)
    up = np.array(view.up, dtype=float)
    right = _normalize(np.cross(forward, up))
    true_up = np.cross(right, forward)

    pose = np.eye(4)
    pose[:3, 0] = right
    pose[:3, 1] = true_up
    pose[:3, 2] = -forward
    pose[:3, 3] = eye
    return pose, distance
