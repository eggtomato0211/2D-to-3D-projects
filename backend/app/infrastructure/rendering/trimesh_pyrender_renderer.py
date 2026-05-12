"""trimesh + pyrender (OSMesa headless) で STL を 4 視点 raster に変換する。

VLM が立体感を確認するための補助画像を出力する。
"""
from __future__ import annotations

import os
# OSMesa を pyopengl のバックエンドに（pyrender import 前に必須）
os.environ.setdefault("PYOPENGL_PLATFORM", "osmesa")

# Python 3.10+ で削除された参照を pyglet 1.x が使うので互換 alias を貼る
import collections
import collections.abc as _cabc
for _name in (
    "Mapping", "MutableMapping", "Iterable", "Iterator",
    "Sequence", "MutableSequence", "Set", "MutableSet",
    "Hashable", "Sized", "Container", "Callable",
    "KeysView", "ValuesView", "ItemsView",
):
    if not hasattr(collections, _name):
        setattr(collections, _name, getattr(_cabc, _name))

import fractions  # noqa: E402
import math  # noqa: E402
if not hasattr(fractions, "gcd"):
    fractions.gcd = math.gcd  # type: ignore[attr-defined]

import io  # noqa: E402

import numpy as np  # noqa: E402
import pyrender  # noqa: E402
import trimesh  # noqa: E402
from PIL import Image  # noqa: E402

from app.domain.interfaces.shaded_four_view_renderer import IShadedFourViewRenderer  # noqa: E402
from app.domain.value_objects.four_view_image import FourViewImage  # noqa: E402

from .views import BG_COLOR_RGB, IMAGE_SIZE, VIEWS, camera_pose_for_view  # noqa: E402


class TrimeshPyrenderRenderer(IShadedFourViewRenderer):
    """STL → 4 視点 PNG（影付き raster）"""

    def __init__(self, image_size: tuple[int, int] = IMAGE_SIZE) -> None:
        self._image_size = image_size

    def render(self, stl_path: str) -> FourViewImage:
        mesh = trimesh.load(stl_path, force="mesh")
        bbox_min, bbox_max = mesh.bounds
        center = (bbox_min + bbox_max) / 2.0
        extent = np.array(bbox_max - bbox_min)
        diag = float(np.linalg.norm(extent))

        scene = pyrender.Scene(
            bg_color=[*BG_COLOR_RGB, 1.0],
            ambient_light=[0.35, 0.35, 0.35],
        )
        scene.add(pyrender.Mesh.from_trimesh(mesh, smooth=False))

        light = pyrender.DirectionalLight(color=np.ones(3), intensity=4.0)
        light_pose = np.eye(4)
        light_pose[:3, 3] = center + np.array([1.0, -1.0, 1.0]) * diag
        scene.add(light, pose=light_pose)

        renderer = pyrender.OffscreenRenderer(
            viewport_width=self._image_size[0],
            viewport_height=self._image_size[1],
        )
        try:
            view_to_png: dict[str, bytes] = {}
            for view in VIEWS:
                pose, _distance = camera_pose_for_view(view, center, diag)
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
                        yfov=np.deg2rad(35.0), znear=znear, zfar=zfar,
                    )
                cam_node = scene.add(cam, pose=pose)
                try:
                    color, _depth = renderer.render(scene)
                    buf = io.BytesIO()
                    Image.fromarray(color).save(buf, format="PNG")
                    view_to_png[view.name] = buf.getvalue()
                finally:
                    scene.remove_node(cam_node)
        finally:
            renderer.delete()

        return FourViewImage(
            top=view_to_png["top"],
            front=view_to_png["front"],
            side=view_to_png["side"],
            iso=view_to_png["iso"],
        )
