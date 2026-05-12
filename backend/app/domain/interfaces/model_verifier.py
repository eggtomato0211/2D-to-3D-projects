"""生成 3D モデルと元図面を比較する検証エンジンのインターフェース。"""
from abc import ABC, abstractmethod

from ..value_objects.four_view_image import FourViewImage
from ..value_objects.verification import VerificationResult


class IModelVerifier(ABC):
    """VLM などで画像比較を行い、不一致を構造化して返すインターフェース。

    具体実装は infrastructure/verification/ に置く。
    """

    @abstractmethod
    def verify(
        self,
        blueprint_image_path: str,
        line_views: FourViewImage,
        shaded_views: FourViewImage,
    ) -> VerificationResult:
        """元 2D 図面 + 生成モデルの 4 視点画像を比較し、不一致を返す。"""
        ...
