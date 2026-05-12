"""STL を入力に影付き raster 4 視点画像を生成するレンダラのインターフェース。"""
from abc import ABC, abstractmethod

from ..value_objects.four_view_image import FourViewImage


class IShadedFourViewRenderer(ABC):
    """trimesh + pyrender などで shaded raster を出力するレンダラ。"""

    @abstractmethod
    def render(self, stl_path: str) -> FourViewImage:
        """STL ファイルパスを受け取り、4 視点 PNG を返す。"""
        ...
