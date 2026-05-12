"""バリアントを CadQuery で生成 → A (shaded) / D (line) でレンダリング。

render_compare の方式 A / D ロジックを再利用する。
"""
from __future__ import annotations

import sys
from pathlib import Path

import cadquery as cq

# 親ディレクトリの render_compare を import 可能にする
EXPERIMENTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(EXPERIMENTS_DIR / "render_compare"))

# render_compare 側のモジュールを再利用
from method_a_trimesh_pyrender import render as render_shaded  # noqa: E402
from method_d_cadquery_svg import render as _render_d_unused   # noqa: E402,F401

# D 側は Workplane を直接使うので、shared 経由ではなく自前で再実装
import cairosvg  # noqa: E402

# render_compare の shared から view 定義を借りる
sys.path.insert(0, str(EXPERIMENTS_DIR / "render_compare"))
from shared import IMAGE_SIZE, VIEWS  # noqa: E402


def export_stl(script: str, stl_path: Path) -> None:
    """CadQuery script を実行して STL を書き出す"""
    namespace: dict = {}
    exec(script, namespace)
    if "result" not in namespace:
        raise RuntimeError("script must define 'result'")
    stl_path.parent.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(namespace["result"], str(stl_path))


def get_workplane(script: str):
    namespace: dict = {}
    exec(script, namespace)
    return namespace["result"]


def render_line_drawings(workplane, out_dir: Path) -> list[Path]:
    """方式 D: CadQuery SVG → cairosvg で 4 視点 PNG を出力"""
    out_dir.mkdir(parents=True, exist_ok=True)
    output: list[Path] = []
    for view in VIEWS:
        opts = {
            "width": IMAGE_SIZE[0],
            "height": IMAGE_SIZE[1],
            "marginLeft": 50,
            "marginTop": 50,
            "showAxes": False,
            "projectionDir": view.eye_dir,
            "strokeWidth": 0.5,
            "strokeColor": (0, 0, 0),
            "hiddenColor": (160, 160, 160),
            "showHidden": True,
        }
        svg_path = out_dir / f"{view.name}.svg"
        png_path = out_dir / f"{view.name}.png"
        cq.exporters.export(workplane, str(svg_path), opt=opts)
        cairosvg.svg2png(
            url=str(svg_path),
            write_to=str(png_path),
            output_width=IMAGE_SIZE[0],
            output_height=IMAGE_SIZE[1],
            background_color="white",
        )
        output.append(png_path)
    return output


def render_both(script: str, base_out_dir: Path) -> dict:
    """1 つのスクリプトに対して shaded (A) と line (D) を両方レンダリング"""
    base_out_dir.mkdir(parents=True, exist_ok=True)
    stl_path = base_out_dir / "model.stl"
    export_stl(script, stl_path)

    shaded_dir = base_out_dir / "shaded"
    line_dir = base_out_dir / "line"

    shaded_files = render_shaded(stl_path, shaded_dir)
    workplane = get_workplane(script)
    line_files = render_line_drawings(workplane, line_dir)

    return {
        "stl": stl_path,
        "shaded": {p.stem: p for p in shaded_files},
        "line": {p.stem: p for p in line_files},
    }
