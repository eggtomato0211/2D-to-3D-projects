"""Analyzer の VLM 応答 (JSON) をパースして DesignStep / Clarification に変換する。

dimensions_table / feature_inventory が含まれていれば、参照情報の先頭ステップに
埋め込み、後段の base_script_generator がそれを認識して RAG クエリ等に活用する。
"""
from __future__ import annotations

import json
import re
from typing import Any

from loguru import logger

from app.domain.value_objects.clarification import (
    Clarification,
    ClarificationAnswer,
    CustomAnswer,
    NoAnswer,
    YesAnswer,
)
from app.domain.value_objects.design_step import DesignStep


_FENCE_RE = re.compile(r"```(?:json)?\s*\n(.*?)```", re.DOTALL)


def extract_json(content: str) -> str:
    fence = _FENCE_RE.search(content)
    if fence:
        return fence.group(1).strip()
    start = content.find("{")
    end = content.rfind("}")
    if start != -1 and end > start:
        return content[start : end + 1]
    return content.strip()


def _parse_answer(raw: Any) -> ClarificationAnswer | None:
    if not isinstance(raw, dict):
        return None
    kind = raw.get("kind")
    if kind == "yes":
        return YesAnswer()
    if kind == "no":
        return NoAnswer()
    if kind == "custom":
        text = raw.get("text")
        if isinstance(text, str) and text.strip():
            return CustomAnswer(text=text.strip())
    return None


def _format_context_step(
    dimensions: list[dict], features: list[dict]
) -> str | None:
    """構造化抽出結果を参照情報ブロックの Markdown に整形する。"""
    if not dimensions and not features:
        return None

    lines = [
        "**【参照情報・このステップは CadQuery 操作ではありません】**"
        " 図面から構造化抽出した寸法と特徴の一覧。"
        "次のステップ以降で本テーブルの数値を `D_outer = 50` 等の変数または"
        "リテラルとして使うこと。"
    ]

    if dimensions:
        lines.append("\n### 寸法表 (dimensions_table)")
        lines.append("| symbol | value | unit | type | source_view | applied_to |")
        lines.append("|---|---|---|---|---|---|")
        for d in dimensions:
            if not isinstance(d, dict):
                continue
            lines.append(
                "| " + " | ".join(str(d.get(k, "")) for k in
                                  ("symbol", "value", "unit", "type", "source_view", "applied_to")) + " |"
            )

    if features:
        lines.append("\n### 特徴インベントリ (feature_inventory)")
        for f in features:
            if not isinstance(f, dict):
                continue
            name = f.get("name", "?")
            ftype = f.get("type", "?")
            count = f.get("count", 1)
            dims = f.get("dimensions", [])
            pos = f.get("position", {})
            note = f.get("note", "")
            bullet = f"- **{name}** (type={ftype}, count={count}"
            if dims:
                bullet += f", dims={dims}"
            if pos:
                bullet += f", pos={pos}"
            bullet += ")"
            if note:
                bullet += f" — {note}"
            lines.append(bullet)

    return "\n".join(lines)


def parse_analyzer_response(
    content: str, include_context_step: bool = True
) -> tuple[list[DesignStep], list[Clarification]]:
    """LLM 応答テキスト → (steps, clarifications)。

    `include_context_step=True` のとき dimensions_table / feature_inventory が
    あれば、それを Step 1 として先頭に挿入する。
    """
    data = json.loads(extract_json(content))

    clarifications: list[Clarification] = []
    for i, raw in enumerate(data.get("clarifications_needed") or []):
        if isinstance(raw, str):
            question, candidates = raw, ()
        elif isinstance(raw, dict):
            question = raw.get("question", "")
            if not question:
                continue
            parsed = [_parse_answer(c) for c in (raw.get("candidates") or [])]
            candidates = tuple(c for c in parsed if c is not None)
        else:
            continue
        clarifications.append(Clarification(
            id=f"clarification_{i + 1}",
            question=question,
            candidates=candidates,
            user_response=None,
        ))

    if clarifications:
        logger.info(f"VLM が {len(clarifications)} 件の確認事項を検出しました")

    context_text = None
    if include_context_step:
        dims = data.get("dimensions_table") or []
        features = data.get("feature_inventory") or []
        context_text = _format_context_step(dims, features)
        if context_text:
            logger.info(
                f"VLM が dimensions_table={len(dims)} 件 / "
                f"feature_inventory={len(features)} 件を抽出しました"
            )

    steps: list[DesignStep] = []
    offset = 0
    if context_text:
        steps.append(DesignStep(step_number=1, instruction=context_text))
        offset = 1
    for step in data.get("steps", []):
        steps.append(DesignStep(
            step_number=int(step["step_number"]) + offset,
            instruction=step["instruction"],
        ))

    return steps, clarifications
