"""Phase 2-δ: 自動修正ループの設定。"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LoopConfig:
    """ループの上限・コスト・挙動を制御する設定。

    Attributes:
        max_iterations:   verify→correct→execute→verify のサイクル回数上限
        cost_budget_usd:  これを超えると諦める（概算ベース）
        detect_degradation: 同イテで critical 件数が増えたら停止
        cost_per_verify_usd:  verify 1 回あたりの推定コスト（cost_budget チェック用）
        cost_per_correct_usd: correct_script 1 回あたりの推定コスト
        single_fix_per_iteration: §10.2 R3 解消用 — True なら critical を 1 件ずつ修正
                                 （連鎖崩壊を回避し、各 iter で確実に 1 件解消する方針）。
                                 1 件ずつなので max_iterations は大きめ推奨。
    """
    max_iterations: int = 5
    cost_budget_usd: float = 1.5
    detect_degradation: bool = True
    cost_per_verify_usd: float = 0.05
    cost_per_correct_usd: float = 0.10  # §10.1 で画像入力したのでコスト増
    single_fix_per_iteration: bool = True
    # §10.6 R3 解消用: 構造化ツール呼び出し型 Corrector を使う
    # True: Tool Use Corrector（add-only、Python テキスト書き換え無し）
    # False: 自然言語 Corrector（既存）
    use_tool_based_correction: bool = False
    # §10.6 改善 a: 連続 K iter で best critical が改善しないなら早期停止
    # （無駄な反復を避けて degradation 前に best を返す）
    # デフォルトは大きい値 = 実質無効。本番デプロイで 1 などに設定する
    early_stop_no_improve_k: int = 999

    def estimate_cycle_cost(self) -> float:
        """1 サイクル（verify + correct + execute）の概算コスト"""
        return self.cost_per_verify_usd + self.cost_per_correct_usd
