"""Phase 2-δ: 各ループ反復のサマリ。CADModel の history に積む。"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

LoopOutcomeT = Literal[
    "in_progress",      # まだループ中
    "success",          # critical=0
    "max_iterations",   # 反復上限
    "degradation",      # critical 件数が増加
    "execute_failed",   # CadQuery 実行が error-fix loop でも失敗
    "correct_failed",   # correct_script が例外
    "budget_exceeded",  # コスト上限
    "no_improvement",   # §10.6 改善 a: K iter 連続で best が改善しないため早期停止
]


@dataclass(frozen=True)
class VerificationSnapshot:
    """1 イテレーション分の結果サマリ"""
    iteration: int
    is_valid: bool
    critical_count: int
    major_count: int
    minor_count: int
    timestamp: datetime
    outcome: LoopOutcomeT = "in_progress"
