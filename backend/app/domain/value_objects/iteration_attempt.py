"""§10.3 R5 解消用: ループ各 iter での試行記録。

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
        tried_discrepancies: その iter で直そうとした不一致（Corrector に渡した分）
        result_discrepancies: その iter の修正後 verify が返した不一致
                              （次 iter 開始時点で見つかった残差）
    """
    iteration: int
    tried_discrepancies: tuple[Discrepancy, ...]
    result_discrepancies: tuple[Discrepancy, ...]
