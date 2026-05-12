"""元 2D 図面と候補 4 視点の line drawing からシルエット IoU を計算するインターフェース。

ベンチの match_score (GT 3D との Volume IoU) の代替として、UI フローで
「VLM verifier が OK と言ったが実際の形状が乖離している」ケースを検知する。
"""
from abc import ABC, abstractmethod

from ..value_objects.four_view_image import FourViewImage


class ISilhouetteIouCalculator(ABC):

    @abstractmethod
    def compute(
        self, blueprint_image_path: str, candidate_views: FourViewImage
    ) -> float:
        """元 2D 図面と候補の各視点線画のシルエット IoU の最大値を返す (0.0-1.0)。

        厳密な視点対応は行わず「figure に近い視点が 1 つでもあるか」で
        gross な乖離を検出する目的の指標。
        """
        ...
