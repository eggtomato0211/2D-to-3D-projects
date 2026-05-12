"""方式 A: trimesh + pyrender (OSMesa headless)

特徴:
- Pure Python パイプライン、軽量
- pyrender の OffscreenRenderer で headless 動作（PYOPENGL_PLATFORM=osmesa）
- 影付き / 陰影あり のレンダリング
"""
from __future__ import annotations

import os
# OSMesa を pyopengl のバックエンドに指定（import 前に設定すること）
os.environ.setdefault("PYOPENGL_PLATFORM", "osmesa")

# Python 3.10+ で collections.Mapping 等が削除されたが、pyglet 1.x が古い参照を持つ。
# pyrender が pyglet 経由でこれを引くので import 前に互換 alias を貼る
import collections
import collections.abc as _cabc
for _name in (
    "Mapping", "MutableMapping",
    "Iterable", "Iterator",
    "Sequence", "MutableSequence",
    "Set", "MutableSet",
    "Hashable", "Sized", "Container", "Callable",
    "KeysView", "ValuesView", "ItemsView",
):
    if not hasattr(collections, _name):
        setattr(collections, _name, getattr(_cabc, _name))

# Python 3.9+ で fractions.gcd が削除されたが pyglet 1.x が参照する
import fractions
import math
if not hasattr(fractions, "gcd"):
    fractions.gcd = math.gcd  # type: ignore[attr-defined]

from pathlib import Path

import numpy as np
import trimesh
import pyrender

from shared import (
    BG_COLOR_RGB,
    IMAGE_SIZE,
    VIEWS,
    camera_pose_for_view,
)


def render(stl_path: Path, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)

    mesh = trimesh.load(stl_path, force="mesh")
    bbox_min, bbox_max = mesh.bounds
    center = (bbox_min + bbox_max) / 2.0
    extent = np.array(bbox_max - bbox_min)
    diag = float(np.linalg.norm(extent))

    scene = pyrender.Scene(
        bg_color=[*BG_COLOR_RGB, 1.0],
        ambient_light=[0.35, 0.35, 0.35],
    )
    pyr_mesh = pyrender.Mesh.from_trimesh(mesh, smooth=False)
    scene.add(pyr_mesh)

    # 主光源（カメラに追従させない、固定方向）
    light = pyrender.DirectionalLight(color=np.ones(3), intensity=4.0)
    light_pose = np.eye(4)
    light_pose[:3, 3] = center + np.array([1, -1, 1]) * diag
    scene.add(light, pose=light_pose)

    renderer = pyrender.OffscreenRenderer(
        viewport_width=IMAGE_SIZE[0],
        viewport_height=IMAGE_SIZE[1],
    )

    output_files: list[Path] = []
    try:
        for view in VIEWS:
            pose, distance = camera_pose_for_view(view, center, diag)
            znear = max(diag * 0.01, 0.01)
            zfar = diag * 10.0
            if view.is_orthographic:
                ortho_extent = max(extent) * 0.6
                cam = pyrender.OrthographicCamera(
                    xmag=ortho_extent, ymag=ortho_extent,
                    znear=znear, zfar=zfar,
                )
            else:
                cam = pyrender.PerspectiveCamera(
                    yfov=np.deg2rad(35.0),
                    znear=znear, zfar=zfar,
                )

            cam_node = scene.add(cam, pose=pose)
            try:
                color, _depth = renderer.render(scene)
                from PIL import Image
                out_path = out_dir / f"{view.name}.png"
                Image.fromarray(color).save(out_path)
                output_files.append(out_path)
            finally:
                scene.remove_node(cam_node)
    finally:
        renderer.delete()

    return output_files


if __name__ == "__main__":
    import sys
    stl = Path(sys.argv[1])
    out = Path(sys.argv[2])
    files = render(stl, out)
    for f in files:
        print(f)
