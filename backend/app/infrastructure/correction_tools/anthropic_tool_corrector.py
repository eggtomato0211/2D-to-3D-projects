"""§10.6 Tool Use 化: Anthropic tool use API を使う Corrector 実装。

LLM は CadQuery のテキストを書かず、構造化ツール呼び出しを返す。
サーバ側でツール呼び出しを CadQuery コード片に変換し、既存スクリプトに append する。
これにより R3（コード surgery の脆さ）を抜本的に回避する。
"""
from __future__ import annotations

from typing import Optional

from anthropic import Anthropic
from loguru import logger

from app.domain.value_objects.cad_script import CadScript
from app.domain.value_objects.discrepancy import Discrepancy
from app.domain.value_objects.four_view_image import FourViewImage
from app.domain.value_objects.iteration_attempt import IterationAttempt
from app.domain.value_objects.tool_call_suggestion import ToolCallSuggestion
from app.infrastructure.vlm.anthropic._image_blocks import (
    image_file_block,
    png_bytes_block,
)

from .feature_extractor import (
    extract_existing_features,
    format_existing_features,
)
from .prompts import TOOL_USE_SYSTEM, build_tool_use_user_text
from .tools import execute_tool_call, get_tool_definitions, signature_for_call


class AnthropicToolBasedCorrector:
    """Tool use API で構造化ツール呼び出しを受け取り、既存 script に append する。

    既存スクリプトを保持したまま「不足する特徴を追加する」操作のみ行う。
    削除・書き換えはできない（add-only 設計）。
    """

    def __init__(self, api_key: str, model: str = "claude-opus-4-7") -> None:
        self._client = Anthropic(api_key=api_key)
        self._model = model

    # ------------------------------------------------------------------
    # 内部ヘルパ
    # ------------------------------------------------------------------
    @staticmethod
    def _format_discrepancies(discrepancies: tuple[Discrepancy, ...]) -> str:
        crit = [d for d in discrepancies if d.severity == "critical"]
        major = [d for d in discrepancies if d.severity == "major"]
        minor = [d for d in discrepancies if d.severity == "minor"]
        lines: list[str] = []
        for label, items in (("Critical", crit), ("Major", major), ("Minor", minor)):
            if not items:
                continue
            lines.append(f"\n### {label} ({len(items)} 件)")
            for i, d in enumerate(items, 1):
                line = f"{i}. **{d.feature_type}**: {d.description}"
                line += f"\n   - 期待: {d.expected}"
                line += f"\n   - 現状: {d.actual}"
                if d.location_hint:
                    line += f"\n   - 位置: {d.location_hint}"
                if d.dimension_hint:
                    line += f"\n   - 寸法: {d.dimension_hint}"
                lines.append(line)
        return "\n".join(lines)

    @staticmethod
    def _format_history(iteration_history: Optional[tuple[IterationAttempt, ...]]) -> str:
        if not iteration_history:
            return ""
        lines = ["\n## 過去の試行履歴"]
        for h in iteration_history:
            tried = ", ".join(
                f"{d.feature_type}({d.severity})" for d in h.tried_discrepancies
            ) or "(なし)"
            rem = ", ".join(
                f"{d.feature_type}({d.severity})" for d in h.result_discrepancies
            ) or "(解消)"
            lines.append(f"- iter {h.iteration}: 修正対象=[{tried}] → 修正後の残差=[{rem}]")
        lines.append("解消できなかった項目は別の数値・位置で試すこと。")
        return "\n".join(lines)

    def _build_message_content(
        self,
        script: CadScript,
        discrepancies: tuple[Discrepancy, ...],
        blueprint_image_path: Optional[str],
        line_views: Optional[FourViewImage],
        shaded_views: Optional[FourViewImage],
        iteration_history: Optional[tuple[IterationAttempt, ...]],
    ) -> list[dict]:
        disc_block = self._format_discrepancies(discrepancies)
        history_block = self._format_history(iteration_history)
        existing_block = format_existing_features(script.content)
        user_text = build_tool_use_user_text(
            script.content, disc_block, history_block + "\n" + existing_block,
        )
        content: list[dict] = []
        if blueprint_image_path is not None:
            content.append({"type": "text", "text": "## reference (original 2D drawing)"})
            content.append(image_file_block(blueprint_image_path))
        if line_views is not None:
            content.append({"type": "text", "text": "## candidate — line drawings (top, front, side, iso)"})
            for png in line_views.as_list():
                content.append(png_bytes_block(png))
        if shaded_views is not None:
            content.append({"type": "text", "text": "## candidate — shaded renderings (top, front, side, iso)"})
            for png in shaded_views.as_list():
                content.append(png_bytes_block(png))
        content.append({"type": "text", "text": user_text})
        return content

    def _request_tool_calls(
        self,
        script: CadScript,
        discrepancies: tuple[Discrepancy, ...],
        blueprint_image_path: Optional[str],
        line_views: Optional[FourViewImage],
        shaded_views: Optional[FourViewImage],
        iteration_history: Optional[tuple[IterationAttempt, ...]],
    ) -> tuple[list[dict], list[str]]:
        """Anthropic Tool Use API を呼び、(tool_calls, text_blocks) を返す。"""
        content = self._build_message_content(
            script, discrepancies, blueprint_image_path,
            line_views, shaded_views, iteration_history,
        )
        msg = self._client.messages.create(
            model=self._model,
            max_tokens=4096,
            system=TOOL_USE_SYSTEM,
            tools=get_tool_definitions(),
            messages=[{"role": "user", "content": content}],
        )
        tool_calls: list[dict] = []
        text_blocks: list[str] = []
        for block in msg.content:
            if getattr(block, "type", None) == "tool_use":
                tool_calls.append({"name": block.name, "input": dict(block.input)})
            elif hasattr(block, "text"):
                text_blocks.append(block.text)
        logger.info(
            f"[tool_correct] model={self._model} "
            f"in={msg.usage.input_tokens} out={msg.usage.output_tokens} "
            f"tools_called={len(tool_calls)}"
        )
        for tc in tool_calls:
            logger.info(f"  -> {tc['name']}({tc['input']})")
        return tool_calls, text_blocks

    # ------------------------------------------------------------------
    # 自動修正（既存）: LLM 呼び出し → dedup → 適用 → 新スクリプト返却
    # ------------------------------------------------------------------
    def correct_script(
        self,
        script: CadScript,
        discrepancies: tuple[Discrepancy, ...],
        blueprint_image_path: Optional[str] = None,
        line_views: Optional[FourViewImage] = None,
        shaded_views: Optional[FourViewImage] = None,
        iteration_history: Optional[tuple[IterationAttempt, ...]] = None,
    ) -> CadScript:
        if not discrepancies:
            return script

        tool_calls, text_blocks = self._request_tool_calls(
            script, discrepancies, blueprint_image_path,
            line_views, shaded_views, iteration_history,
        )
        if not tool_calls:
            if text_blocks:
                logger.warning(f"[tool_correct] no tool calls; text head: {text_blocks[0][:200]}")
            return script

        # dedup 適用
        return self.apply_tool_calls(script, tool_calls, dedup_against_existing=True)

    # ------------------------------------------------------------------
    # §11.5 Human-in-the-loop: 提案だけ返す（適用しない）
    # ------------------------------------------------------------------
    def suggest_tool_calls(
        self,
        script: CadScript,
        discrepancies: tuple[Discrepancy, ...],
        blueprint_image_path: Optional[str] = None,
        line_views: Optional[FourViewImage] = None,
        shaded_views: Optional[FourViewImage] = None,
        iteration_history: Optional[tuple[IterationAttempt, ...]] = None,
    ) -> list[ToolCallSuggestion]:
        """LLM に「もし修正するならどのツールを呼ぶか」を提案させ、ToolCallSuggestion として返す。

        この時点では script への適用は行わない。ユーザーが UI で確認・選択して
        apply_tool_calls() を呼ぶ流れを想定している。
        """
        if not discrepancies:
            return []

        tool_calls, _text = self._request_tool_calls(
            script, discrepancies, blueprint_image_path,
            line_views, shaded_views, iteration_history,
        )
        # discrepancy 索引と推測でリンク（ヒューリスティック: feature_type 一致）
        suggestions: list[ToolCallSuggestion] = []
        existing_features = set(extract_existing_features(script.content))
        for tc in tool_calls:
            sig = signature_for_call(tc["name"], tc["input"])
            is_dup = sig is not None and sig in existing_features
            related_idx = self._find_related_discrepancy(tc["name"], discrepancies)
            rationale = (
                "重複（既存特徴とシグネチャ一致、適用しても効果なし）"
                if is_dup else "LLM が推奨する修正候補"
            )
            suggestions.append(ToolCallSuggestion(
                tool_name=tc["name"],
                args=tc["input"],
                related_discrepancy_index=related_idx,
                rationale=rationale,
            ))
        return suggestions

    @staticmethod
    def _find_related_discrepancy(
        tool_name: str, discrepancies: tuple[Discrepancy, ...],
    ) -> int | None:
        """ツール名 → 対応する Discrepancy の index を推測"""
        feature_to_tools = {
            "hole":    {"add_hole", "add_pcd_holes", "add_counterbore",
                        "add_pcd_counterbores", "fill_circular_hole",
                        "resize_central_hole"},
            "thread":  {"add_hole", "add_pcd_holes"},
            "slot":    {"cut_obround_slot", "replace_central_hole_with_obround_slot"},
            "boss":    {"add_step_boss"},
            "step":    {"add_step_boss", "add_recess"},
            "chamfer": {"add_chamfer_top_bottom"},
            "fillet":  {"add_fillet_vertical_edges"},
            "outline": {"cut_outer_scallops"},
        }
        for i, d in enumerate(discrepancies):
            if tool_name in feature_to_tools.get(d.feature_type, set()):
                return i
        return None

    # ------------------------------------------------------------------
    # §11.5 Human-in-the-loop: ユーザー承認済み tool calls を適用
    # ------------------------------------------------------------------
    def apply_tool_calls(
        self,
        script: CadScript,
        tool_calls: list[dict],
        dedup_against_existing: bool = False,
    ) -> CadScript:
        """与えられた tool calls を CadQuery コードに変換して既存 script に append する。

        Human-in-the-loop で使う: ユーザーが承認した呼び出しのみが渡される想定。
        dedup_against_existing=True にすると既存特徴と重複するものを skip する
        （correct_script 内部で使用、ユーザー承認済みなら通常は False）。
        """
        if not tool_calls:
            return script

        existing_features = (
            set(extract_existing_features(script.content))
            if dedup_against_existing else set()
        )
        appended_code: list[str] = []
        skipped: list[dict] = []
        for tc in tool_calls:
            sig = signature_for_call(tc["name"], tc["input"])
            if dedup_against_existing and sig is not None and sig in existing_features:
                logger.warning(
                    f"[tool_correct] skip duplicate: {tc['name']}({tc['input']}) "
                    f"matches existing '{sig}'"
                )
                skipped.append(tc)
                continue
            try:
                snippet = execute_tool_call(tc["name"], tc["input"])
                appended_code.append(snippet)
            except Exception as e:
                logger.warning(f"[tool_correct] tool {tc['name']} failed: {e}")
                continue

        if skipped:
            logger.info(
                f"[tool_correct] {len(skipped)}/{len(tool_calls)} calls skipped as duplicates"
            )
        if not appended_code:
            return script

        new_content = script.content.rstrip() + "\n" + "".join(appended_code)
        return CadScript(content=new_content)
