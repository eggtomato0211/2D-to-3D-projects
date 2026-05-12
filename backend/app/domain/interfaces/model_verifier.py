"""生成 3D モデルと参照図面を比較する検証エンジンのインターフェース。"""
from abc import ABC, abstractmethod

from ..value_objects.four_view_image import FourViewImage
from ..value_objects.verification import VerificationResult


class IModelVerifier(ABC):
    """
    生成された 3D モデルと元の図面を比較検証するインターフェース。

    Phase 2 検証フローの中核。VLM などで画像比較を行い、不一致を構造化して返す。
    具体実装は infrastructure/verification/ に置く。
    """

    @abstractmethod
    def verify(
        self,
        blueprint_image_path: str,
        line_views: FourViewImage,
        shaded_views: FourViewImage,
    ) -> VerificationResult:
        """
        Args:
            blueprint_image_path: 元の 2D 図面の画像ファイルパス
            line_views:           生成モデルの線画 4 視点
            shaded_views:         生成モデルの影付き 4 視点

        Returns:
            VerificationResult: 不一致リストを含む検証結果
        """
        ...
