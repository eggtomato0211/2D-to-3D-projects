"""STEP を入力に線画 4 視点画像を生成するレンダラのインターフェース。"""
from abc import ABC, abstractmethod

from ..value_objects.four_view_image import FourViewImage


class ILineDrawingFourViewRenderer(ABC):
    """CadQuery SVG → cairosvg PNG など、隠れ線付きの線画を出力するレンダラ。"""

    @abstractmethod
    def render(self, step_path: str) -> FourViewImage:
        """STEP ファイルパスを受け取り、4 視点 PNG を返す。"""
        ...
