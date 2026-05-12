"""Verify-Correct 自動修正ループの設定。"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LoopConfig:
    """ループの上限・停止条件を制御する設定。

    Attributes:
        max_iterations:        verify→correct→execute→verify のサイクル上限
        single_fix_per_iter:   True なら critical を 1 件ずつ修正
                               （連鎖崩壊を回避し各 iter で確実に解消する方針）
        stop_on_degradation:   critical 件数が増えたら早期停止
    """
    max_iterations: int = 5
    single_fix_per_iter: bool = True
    stop_on_degradation: bool = True
