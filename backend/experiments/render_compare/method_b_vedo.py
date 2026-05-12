"""方式 B: vedo (VTK ラッパ)

特徴:
- VTK ベース、API がシンプル
- Plotter(offscreen=True) で headless 動作
- 影・エッジ強調・色設定が容易
"""
from __future__ import annotations

import os
# vedo (VTK) を確実に offscreen で動かす
os.environ.setdefault("VTK_USE_OFFSCREEN", "1")
os.environ.setdefault("DISPLAY", "")

from pathlib import Path

import numpy as np
import vedo

from shared import IMAGE_SIZE, VIEWS, camera_pose_for_view

# vedo の global 設定で headless / offscreen を強制
vedo.settings.default_backend = "vtk"
vedo.settings.screenshot_transparent_background = False


def render(stl_path: Path, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)

    mesh = vedo.Mesh(str(stl_path))
    mesh.color("lightblue").lw(0.5).lighting("default")

    bbox = mesh.bounds()
    bbox_min = np.array([bbox[0], bbox[2], bbox[4]])
    bbox_max = np.array([bbox[1], bbox[3], bbox[5]])
    center = (bbox_min + bbox_max) / 2.0
    diag = float(np.linalg.norm(bbox_max - bbox_min))

    output_files: list[Path] = []
    for view in VIEWS:
        pose, _distance = camera_pose_for_view(view, center, diag)
        eye = pose[:3, 3]

        cam = dict(
            position=eye.tolist(),
            focal_point=center.tolist(),
            viewup=list(view.up),
        )

        plt = vedo.Plotter(
            offscreen=True,
            size=IMAGE_SIZE,
            bg="white",
            interactive=False,
        )

        # 直交投影は VTK の SetParallelProjection で設定する
        if view.is_orthographic:
            plt.parallel_projection(True)

        plt.show(mesh, camera=cam, resetcam=False, interactive=False)

        # 直交投影時のスケール（FocalPoint に対する半幅）
        if view.is_orthographic:
            plt.camera.SetParallelScale(diag * 0.5)
            plt.render()

        out_path = out_dir / f"{view.name}.png"
        plt.screenshot(str(out_path))
        plt.close()
        output_files.append(out_path)

    return output_files


if __name__ == "__main__":
    import sys
    stl = Path(sys.argv[1])
    out = Path(sys.argv[2])
    files = render(stl, out)
    for f in files:
        print(f)
