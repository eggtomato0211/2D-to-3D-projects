"""4 視点（top / front / side / iso）のカメラ規約。

JIS B 0001 第三角法に準拠:
- top:   +Z 方向から見下ろす（平面図）
- front: -Y 方向から見る（正面図）
- side:  +X 方向から見る（右側面図）
- iso:   (+1, -1, +1) 方向の等角投影
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

IMAGE_SIZE: tuple[int, int] = (1024, 1024)
BG_COLOR_RGB: tuple[float, float, float] = (1.0, 1.0, 1.0)


@dataclass(frozen=True)
class ViewSpec:
    name: str
    eye_dir: tuple[float, float, float]
    up: tuple[float, float, float]
    is_orthographic: bool


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
    """OpenGL / pyrender 互換の camera-to-world transform を返す。"""
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
