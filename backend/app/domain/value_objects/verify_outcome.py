"""Phase 2-δ §10.1 用: 検証結果 + 視覚情報を一緒に運ぶ値オブジェクト。

VerifyCadModelUseCase は判定（VerificationResult）に加えて、レンダリング済みの
4 視点画像と、参照図面のパスを VerifyOutcome として返す。
これにより VerifyAndCorrectUseCase は再レンダリング無しで Corrector に画像を渡せる。
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
