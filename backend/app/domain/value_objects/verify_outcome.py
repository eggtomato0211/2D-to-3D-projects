"""検証結果 + 視覚情報をひとまとめにする値オブジェクト。

VerifyCadModelUseCase はレンダリング済みの 4 視点画像と参照図面パスを
VerifyOutcome として返す。これにより VerifyAndCorrectUseCase は
再レンダリング無しで Corrector に画像を渡せる。
"""
from __future__ import annotations

from dataclasses import dataclass

from .four_view_image import FourViewImage
from .verification import VerificationResult


@dataclass(frozen=True)
class VerifyOutcome:
    result: VerificationResult
    line_views: FourViewImage
    shaded_views: FourViewImage
    blueprint_image_path: str
