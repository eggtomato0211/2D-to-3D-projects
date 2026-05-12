"""§11.5 Human-in-the-loop: LLM が提案する修正候補ツール呼び出し。

ユーザーが UI で確認・編集・承認できるよう、構造化された 1 件の提案として表現する。
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ToolCallSuggestion:
    """1 件の tool call 提案。

    Attributes:
        tool_name: 呼び出すツール名（例: "add_pcd_holes"）
        args:      ツールに渡す引数（dict）
        related_discrepancy_index: この提案が解消しようとしている Discrepancy の
                                   インデックス（VerificationResult.discrepancies 内）。
                                   None の場合は特定の不一致と紐付けない（任意提案）。
        rationale: なぜこのツールを呼ぶのかの説明（人間用、LLM 出力 or サーバ生成）
    """
    tool_name: str
    args: dict
    related_discrepancy_index: int | None = None
    rationale: str = ""
