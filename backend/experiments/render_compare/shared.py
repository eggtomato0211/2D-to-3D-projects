"""4 方式のレンダラ比較で共有する設定・ヘルパ。

設計方針:
- 同一の STL を入力として、各方式が同じ 4 視点 (top/front/side/iso) を出力する
- 視点はメッシュの bounding box から自動計算（モデル依存しない）
- 解像度・背景色は固定して比較条件を揃える
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np

IMAGE_SIZE = (1024, 1024)
BG_COLOR_RGB = (1.0, 1.0, 1.0)

VIEW_NAMES = ("top", "front", "side", "iso")


@dataclass(frozen=True)
class ViewSpec:
    name: str
    eye_dir: tuple[float, float, float]   # camera position direction (unit vec)
    up: tuple[float, float, float]
    is_orthographic: bool                  # True: ortho (top/front/side), False: persp (iso)


VIEWS: tuple[ViewSpec, ...] = (
    ViewSpec("top",   (0.0, 0.0, 1.0),  (0.0, 1.0, 0.0), True),
    ViewSpec("front", (0.0, -1.0, 0.0), (0.0, 0.0, 1.0), True),
    ViewSpec("side",  (1.0, 0.0, 0.0),  (0.0, 0.0, 1.0), True),
    ViewSpec("iso",   (1.0, -1.0, 1.0), (0.0, 0.0, 1.0), False),
)


def normalize(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v)
    if n < 1e-12:
        return v
    return v / n


def camera_pose_for_view(
    view: ViewSpec,
    bbox_center: np.ndarray,
    bbox_diag: float,
) -> tuple[np.ndarray, float]:
    """カメラの 4x4 world transform と target までの距離を返す。

    transform の規約は OpenGL/pyrender 互換: -Z 方向を見る。
    """
    direction = normalize(np.array(view.eye_dir, dtype=float))
    distance = bbox_diag * 1.6
    eye = bbox_center + direction * distance

    forward = normalize(bbox_center - eye)        # camera looks toward target
    up = np.array(view.up, dtype=float)
    right = normalize(np.cross(forward, up))
    true_up = np.cross(right, forward)

    pose = np.eye(4)
    pose[:3, 0] = right
    pose[:3, 1] = true_up
    pose[:3, 2] = -forward
    pose[:3, 3] = eye
    return pose, distance


# ---- テストモデル: CadQuery で生成 ------------------------------------------------
TEST_MODEL_SCRIPT = """\
import cadquery as cq
# 各 workplane を bbox 中心に固定する（face centroid を使うと先に空けた穴で
# centroid が偏り、後続の center(-25, 0) が想定外の位置になるため）
result = (
    cq.Workplane("XY")
    .box(80, 50, 20)
    .faces(">Z").workplane(centerOption="CenterOfBoundBox").hole(12)
    .faces(">Z").workplane(centerOption="CenterOfBoundBox").center(25, 0).hole(6)
    .faces(">Z").workplane(centerOption="CenterOfBoundBox").center(-25, 0).hole(6)
    .edges("|Z").fillet(3)
    .edges(">Z or <Z").chamfer(0.5)
)
"""


def export_test_stl(out_path: Path) -> Path:
    """テストモデルを CadQuery で生成し STL に書き出す"""
    import cadquery as cq  # noqa: F401  # used in exec

    namespace: dict = {}
    exec(TEST_MODEL_SCRIPT, namespace)
    result = namespace["result"]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(result, str(out_path))
    return out_path


def export_test_step(out_path: Path) -> Path:
    """テストモデルを CadQuery で生成し STEP に書き出す（D 方式 SVG エクスポート用）"""
    import cadquery as cq

    namespace: dict = {}
    exec(TEST_MODEL_SCRIPT, namespace)
    result = namespace["result"]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(result, str(out_path))
    return out_path


def get_test_workplane():
    """D 方式が直接 Workplane を欲しがるので、共有して再生成しないよう返す"""
    namespace: dict = {}
    exec(TEST_MODEL_SCRIPT, namespace)
    return namespace["result"]
