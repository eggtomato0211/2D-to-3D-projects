"""LLM に渡すユーザープロンプトの組立。

generate / fix / correct / modify_parameters のそれぞれに対応する
ビルダー関数を提供する。RAG 抜粋やクラリフィケーションの注入も担う。
"""
from __future__ import annotations

from typing import Optional

from app.domain.value_objects.cad_script import CadScript
from app.domain.value_objects.clarification import (
    Clarification,
    ClarificationAnswer,
    CustomAnswer,
    NoAnswer,
    YesAnswer,
)
from app.domain.value_objects.design_step import DesignStep
from app.domain.value_objects.discrepancy import Discrepancy
from app.domain.value_objects.iteration_attempt import IterationAttempt
from app.domain.value_objects.model_parameter import ModelParameter

from ._error_hints import error_hints_for

_REFERENCE_PREFIX = "**【参照情報"


def _answer_to_text(answer: ClarificationAnswer) -> str:
    match answer:
        case YesAnswer():
            return "はい"
        case NoAnswer():
            return "いいえ"
        case CustomAnswer(text=text):
            return text


def _split_reference_blocks(steps: list[DesignStep]) -> tuple[list[str], list[DesignStep]]:
    """先頭の参照情報ブロックを設計手順から分離する。"""
    references: list[str] = []
    operations: list[DesignStep] = []
    for step in steps:
        if step.instruction.startswith(_REFERENCE_PREFIX):
            references.append(step.instruction)
        else:
            operations.append(step)
    return references, operations


def build_intent_prompt(
    steps: list[DesignStep],
    clarifications: list[Clarification],
    docs_block: str = "",
    reference_block: str = "",
) -> str:
    """設計手順 + 確認事項 + RAG 抜粋を 1 つのプロンプトに組み立てる。

    Args:
        docs_block:      CadQuery 公式 docs RAG の抜粋（空文字なら未注入）
        reference_block: 類似 GT 部品の操作列（空文字なら未注入）
    """
    references, operations = _split_reference_blocks(steps)
    steps_text = "\n".join(
        f"{i}. {step.instruction}" for i, step in enumerate(operations, 1)
    )

    parts: list[str] = []
    if docs_block:
        parts.append("## CadQuery 公式ドキュメント抜粋（API シグネチャ・使用例の根拠として参照）")
        parts.append(docs_block)
    if reference_block:
        parts.append("## 類似 GT 部品の操作列（参照のみ。同じ操作列を真似して CadQuery で書き直すこと）")
        parts.append(reference_block)
    if references:
        parts.append("## 参照情報（コード化しないこと。下記の設計手順から参照される寸法・特徴の事前整理）")
        parts.extend(references)
        parts.append("## 設計手順（実際の CadQuery 操作。各ステップを順に実装すること）")
    else:
        parts.append("以下の設計手順に基づいて、CadQuery スクリプトを生成してください:")
    parts.append(steps_text)

    prompt = "\n\n".join(parts)

    confirmed = [c for c in clarifications if c.user_response is not None]
    if confirmed:
        prompt += "\n\n## 【厳守】ユーザーから確認された設計要件"
        prompt += "\n以下はユーザーが明示的に確認・指定した要件です。"
        prompt += "**絶対に簡略化せず、ユーザーの回答を忠実に反映すること。**"
        prompt += "実装が複雑になっても、ユーザー要件を優先してください。\n"
        for c in confirmed:
            prompt += f"\n- Q: {c.question}"
            prompt += f"\n  A: {_answer_to_text(c.user_response)}"

    return prompt


def build_fix_prompt(script: CadScript, feedback: str) -> str:
    """ランタイムエラー修正用のプロンプト。"""
    return f"""以下の CadQuery スクリプトを実行したところエラーが発生しました。
エラーを修正したスクリプトを生成してください。

## 現在のスクリプト
```python
{script.content}
```

## エラーメッセージ
{feedback}
{error_hints_for(feedback)}
## 修正ルール
- エラーの原因を特定し、該当箇所のみ修正すること（無関係な書き換えは禁止）
- 記憶に頼って存在しないメソッド名を作らないこと
- import cadquery as cq から始めること
- 最終結果は result 変数に代入すること（result = ... の形式）
- コードのみを出力し、説明文は不要
- コードは ```python ``` で囲むこと"""


def _discrepancy_block(label: str, items: list[Discrepancy]) -> str:
    if not items:
        return ""
    lines = [f"\n### {label} ({len(items)} 件)"]
    for i, d in enumerate(items, 1):
        loc = f"\n   - 位置: {d.location_hint}" if d.location_hint else ""
        dim = f"\n   - 寸法: {d.dimension_hint}" if d.dimension_hint else ""
        lines.append(
            f"{i}. **{d.feature_type}**: {d.description}\n"
            f"   - 期待: {d.expected}\n"
            f"   - 現状: {d.actual}"
            f"{loc}{dim}\n"
            f"   - 確信度: {d.confidence}"
        )
    return "\n".join(lines)


def _history_block(history: Optional[tuple[IterationAttempt, ...]]) -> str:
    if not history:
        return ""
    lines = ["\n## 過去の試行履歴（同じアプローチを繰り返さないこと）"]
    for h in history:
        tried = ", ".join(
            f"{d.feature_type}({d.severity})" for d in h.tried
        ) or "(なし)"
        remaining = ", ".join(
            f"{d.feature_type}({d.severity})" for d in h.remaining
        ) or "(なし — 解消)"
        lines.append(
            f"- iter {h.iteration}: 修正対象=[{tried}] → 修正後の残差=[{remaining}]"
        )
    lines.append(
        "上記で **解消できなかった項目** に対しては、前回と異なるアプローチを試すこと。"
    )
    return "\n".join(lines)


def build_correct_prompt(
    script: CadScript,
    discrepancies: tuple[Discrepancy, ...],
    iteration_history: Optional[tuple[IterationAttempt, ...]] = None,
) -> str:
    """形状差分の解消用プロンプト（fix_script とは別系統）。"""
    if not discrepancies:
        raise ValueError("discrepancies が空のとき correct を呼ぶべきではありません")

    critical = [d for d in discrepancies if d.severity == "critical"]
    major = [d for d in discrepancies if d.severity == "major"]
    minor = [d for d in discrepancies if d.severity == "minor"]

    if len(discrepancies) == 1:
        policy = (
            "- **この 1 件の不一致のみを修正すること**"
            "（他の問題は次のループで扱うので無視）"
        )
    else:
        policy = (
            "- **Critical を全て解消すること**（最優先）\n"
            "- Major は可能な範囲で対応\n"
            "- Minor は無理に直さない（過剰な書き換えは禁止）"
        )

    return f"""以下の CadQuery スクリプトは構文的には正しく実行できますが、
生成された 3D モデルが元の図面と一致していません。
**列挙された不一致を解消する修正版スクリプト**を生成してください。

## 現在のスクリプト
```python
{script.content}
```

## 検出された不一致
{_discrepancy_block("Critical（必ず修正）", critical)}{_discrepancy_block("Major（修正すべき）", major)}{_discrepancy_block("Minor（余裕があれば修正）", minor)}
{_history_block(iteration_history)}

## 修正の方針
{policy}
- **不一致に直接関係しない箇所は触らない**（既に図面と合っている特徴を壊さない）
- 寸法・位置は元図面の値を尊重する。`位置`/`寸法` ヒントが提示されている場合は **そのまま使う**

## 出力ルール（厳守）
- import cadquery as cq から始めること
- 最終結果は result 変数に代入すること（result = ... の形式）
- コードのみを出力し、説明文は不要
- コードは ```python ``` で囲むこと
- 既に正しく実装されている特徴を「念のため」改変しないこと
"""


def build_modify_parameters_prompt(
    script: CadScript,
    old_parameters: list[ModelParameter],
    new_parameters: list[ModelParameter],
) -> str:
    """パラメータ変更用のプロンプト。"""
    old_map = {p.name: p for p in old_parameters}
    changes: list[str] = []
    for new_p in new_parameters:
        old_p = old_map.get(new_p.name)
        if old_p and old_p.value != new_p.value:
            changes.append(
                f"- {new_p.name} ({new_p.parameter_type.value}): "
                f"{old_p.value} mm → {new_p.value} mm"
            )

    return f"""以下の CadQuery スクリプトのパラメータ（寸法）を変更してください。

## 現在のスクリプト
```python
{script.content}
```

## 変更するパラメータ
{chr(10).join(changes)}

## ルール
- 指定されたパラメータに対応するスクリプト内の数値を変更すること
- パラメータ変更に伴い、他の寸法も整合性を保つよう調整すること
- import cadquery as cq から始めること
- 最終結果は result 変数に代入すること
- コードのみを出力し、説明文は不要
- コードは ```python ``` で囲むこと"""
