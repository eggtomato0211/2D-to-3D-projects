"""Verify-Correct 自動修正ループの設定。"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LoopConfig:
    """ループの上限・停止条件を制御する設定。

    Attributes:
        max_iterations:           verify→correct→execute→verify のサイクル上限
        single_fix_per_iter:      True なら critical を 1 件ずつ修正
                                  （連鎖崩壊を回避し各 iter で確実に解消する方針）
        stop_on_degradation:      True にすると critical 件数が増えた瞬間に
                                  ループを break する。既定 False で
                                  「critical=0 を達成するか max_iterations 到達まで
                                  粘る」挙動。best 状態は常に track されるので、
                                  途中で悪化しても返却結果は最良のものになる
        silhouette_check_enabled: VLM verifier に加えてシルエット IoU でも判定
        silhouette_iou_threshold: この値未満なら verifier が valid と言っても
                                  「形状が乖離」とみなして合成 critical を注入
    """
    max_iterations: int = 5
    single_fix_per_iter: bool = True
    stop_on_degradation: bool = False
    silhouette_check_enabled: bool = True
    silhouette_iou_threshold: float = 0.15
