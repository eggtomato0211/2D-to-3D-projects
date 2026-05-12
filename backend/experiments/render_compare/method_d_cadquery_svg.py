"""方式 D: CadQuery SVG エクスポート → cairosvg で PNG 化

特徴:
- CadQuery 内で完結、線図として正確
- 影なし、ワイヤフレーム / 隠れ線表示
- GL ランタイム不要（CPU のみ）
- 図面と直接見比べやすい線画
"""
from __future__ import annotations

from pathlib import Path

import cadquery as cq
import cairosvg

from shared import IMAGE_SIZE, VIEWS, get_test_workplane


# CadQuery SVG オプション
# projectionDir: カメラ視線方向（正規化された 3D ベクトル）
# strokeColor / hiddenColor / showHidden 等で線種を制御
def _svg_options(view_name: str, view_dir: tuple[float, float, float]) -> dict:
    return {
        "width": IMAGE_SIZE[0],
        "height": IMAGE_SIZE[1],
        "marginLeft": 50,
        "marginTop": 50,
        "showAxes": False,
        "projectionDir": view_dir,
        "strokeWidth": 0.5,
        "strokeColor": (0, 0, 0),
        "hiddenColor": (160, 160, 160),
        "showHidden": True,
    }


def render(stl_path_unused: Path, out_dir: Path) -> list[Path]:
    """SVG 経路では STL ではなく Workplane を直接使う（線画として正確）"""
    del stl_path_unused
    out_dir.mkdir(parents=True, exist_ok=True)

    workplane = get_test_workplane()

    output_files: list[Path] = []
    for view in VIEWS:
        opts = _svg_options(view.name, view.eye_dir)

        svg_path = out_dir / f"{view.name}.svg"
        png_path = out_dir / f"{view.name}.png"

        cq.exporters.export(
            workplane,
            str(svg_path),
            opt=opts,
        )
        cairosvg.svg2png(
            url=str(svg_path),
            write_to=str(png_path),
            output_width=IMAGE_SIZE[0],
            output_height=IMAGE_SIZE[1],
            background_color="white",
        )
        output_files.append(png_path)

    return output_files


if __name__ == "__main__":
    import sys
    stl = Path(sys.argv[1])
    out = Path(sys.argv[2])
    files = render(stl, out)
    for f in files:
        print(f)
