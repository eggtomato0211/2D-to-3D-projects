"""方式 C: Open3D (OffscreenRenderer)

特徴:
- 高品質レンダリング、メッシュ操作も可
- パッケージサイズ大（~300MB）
- OffscreenRenderer を使う（EGL or OSMesa）
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import open3d as o3d
from open3d.visualization import rendering

from shared import BG_COLOR_RGB, IMAGE_SIZE, VIEWS, camera_pose_for_view


def render(stl_path: Path, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)

    mesh = o3d.io.read_triangle_mesh(str(stl_path))
    mesh.compute_vertex_normals()

    bbox = mesh.get_axis_aligned_bounding_box()
    bbox_min = np.asarray(bbox.min_bound)
    bbox_max = np.asarray(bbox.max_bound)
    center = (bbox_min + bbox_max) / 2.0
    diag = float(np.linalg.norm(bbox_max - bbox_min))

    renderer = rendering.OffscreenRenderer(IMAGE_SIZE[0], IMAGE_SIZE[1])

    mat = rendering.MaterialRecord()
    mat.shader = "defaultLit"
    mat.base_color = [0.65, 0.75, 0.85, 1.0]

    renderer.scene.set_background([*BG_COLOR_RGB, 1.0])
    renderer.scene.add_geometry("mesh", mesh, mat)
    renderer.scene.scene.set_sun_light(
        [0.577, -0.577, -0.577],
        [1.0, 1.0, 1.0],
        75000,
    )
    renderer.scene.scene.enable_sun_light(True)

    output_files: list[Path] = []
    try:
        for view in VIEWS:
            pose, _distance = camera_pose_for_view(view, center, diag)
            eye = pose[:3, 3].tolist()

            if view.is_orthographic:
                renderer.scene.camera.set_projection(
                    rendering.Camera.Projection.Ortho,
                    -diag * 0.5, diag * 0.5,
                    -diag * 0.5, diag * 0.5,
                    diag * 0.1, diag * 5.0,
                )
            else:
                renderer.scene.camera.set_projection(
                    35.0,
                    IMAGE_SIZE[0] / IMAGE_SIZE[1],
                    diag * 0.1,
                    diag * 5.0,
                    rendering.Camera.FovType.Vertical,
                )
            renderer.scene.camera.look_at(
                center.tolist(),
                eye,
                list(view.up),
            )

            img = renderer.render_to_image()
            out_path = out_dir / f"{view.name}.png"
            o3d.io.write_image(str(out_path), img, 9)
            output_files.append(out_path)
    finally:
        del renderer

    return output_files


if __name__ == "__main__":
    import sys
    stl = Path(sys.argv[1])
    out = Path(sys.argv[2])
    files = render(stl, out)
    for f in files:
        print(f)
