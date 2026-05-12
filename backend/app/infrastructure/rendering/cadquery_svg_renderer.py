"""STEP → 4 視点 PNG（線画、隠れ線付き）。

CadQuery 内蔵 SVG export → cairosvg で raster 化。
VLM が元 2D 図面と直接比較するための主軸画像を提供する。
"""
from __future__ import annotations

import cadquery as cq
import cairosvg

from app.domain.interfaces.line_drawing_four_view_renderer import (
    ILineDrawingFourViewRenderer,
)
from app.domain.value_objects.four_view_image import FourViewImage

from .views import IMAGE_SIZE, VIEWS


class CadQuerySvgRenderer(ILineDrawingFourViewRenderer):

    def __init__(self, image_size: tuple[int, int] = IMAGE_SIZE) -> None:
        self._image_size = image_size

    def render(self, step_path: str) -> FourViewImage:
        compound = cq.exporters.toCompound(cq.importers.importStep(step_path))

        view_to_png: dict[str, bytes] = {}
        for view in VIEWS:
            opts = {
                "width": self._image_size[0],
                "height": self._image_size[1],
                "marginLeft": 50,
                "marginTop": 50,
                "showAxes": False,
                "projectionDir": view.eye_dir,
                "strokeWidth": 0.5,
                "strokeColor": (0, 0, 0),
                "hiddenColor": (160, 160, 160),
                "showHidden": True,
            }
            svg = cq.exporters.getSVG(compound, opts=opts).encode("utf-8")
            view_to_png[view.name] = cairosvg.svg2png(
                bytestring=svg,
                output_width=self._image_size[0],
                output_height=self._image_size[1],
                background_color="white",
            )

        return FourViewImage(
            top=view_to_png["top"],
            front=view_to_png["front"],
            side=view_to_png["side"],
            iso=view_to_png["iso"],
        )
