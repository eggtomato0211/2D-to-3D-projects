"""ループ各 iter での試行記録。

Corrector が過去の試行と結果を見て「同じ失敗を繰り返さない」よう判断するための情報。
"""
from __future__ import annotations

from dataclasses import dataclass

from .discrepancy import Discrepancy


@dataclass(frozen=True)
class IterationAttempt:
    """1 iter 分の試行と結果のペア。

    Attributes:
        iteration: 何回目の iter か（1-indexed）
        tried:     その iter で直そうとした不一致
        remaining: その iter の修正後に verifier が返した残差
    """
    iteration: int
    tried: tuple[Discrepancy, ...]
    remaining: tuple[Discrepancy, ...]
