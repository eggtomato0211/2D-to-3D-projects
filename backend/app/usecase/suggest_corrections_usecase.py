"""§11.5 Human-in-the-loop: 検証 + 修正候補提示（適用なし）。

VerifyCadModelUseCase で検出した不一致に対して、LLM が呼ぶべきツール群を
提案として返す。実際の適用はユーザー承認後に ApplyToolCallsUseCase で行う。
"""
from __future__ import annotations

from dataclasses import dataclass

from loguru import logger

from app.domain.entities.cad_model import CADModel
from app.domain.interfaces.cad_model_repository import ICADModelRepository
from app.domain.value_objects.tool_call_suggestion import ToolCallSuggestion
from app.domain.value_objects.verification import VerificationResult
from app.usecase.verify_cad_model_usecase import VerifyCadModelUseCase


@dataclass(frozen=True)
class SuggestCorrectionsResult:
    verification: VerificationResult
    suggestions: tuple[ToolCallSuggestion, ...]


class SuggestCorrectionsUseCase:
    """検証実行 + 修正候補生成（適用なし）。

    Human-in-the-loop UI が呼び出す想定:
        1. このユースケースで verification + suggestions を取得
        2. ユーザーが UI で確認・選択
        3. ApplyToolCallsUseCase に承認済み tool calls を渡す
    """

    def __init__(
        self,
        cad_model_repo: ICADModelRepository,
        verify_uc: VerifyCadModelUseCase,
        tool_based_corrector,  # AnthropicToolBasedCorrector
    ) -> None:
        self.cad_model_repo = cad_model_repo
        self.verify_uc = verify_uc
        self.tool_based_corrector = tool_based_corrector

    def execute(self, model_id: str) -> SuggestCorrectionsResult:
        cad_model: CADModel = self.cad_model_repo.get_by_id(model_id)
        if cad_model.cad_script is None:
            raise ValueError(f"CADModel {model_id} に cad_script が無いため修正候補を作れません")

        # 1. 検証（renderers + verifier）
        outcome = self.verify_uc.execute(model_id)
        result = outcome.result
        logger.info(
            f"[suggest {model_id}] verify done: critical={result.critical_count()}, "
            f"major={result.major_count()}, minor={result.minor_count()}"
        )

        # 2. is_valid=True（critical=0）でもユーザーは major/minor を直したいかもしれないので
        #    discrepancies があれば常に suggestions を試みる
        if not result.discrepancies:
            return SuggestCorrectionsResult(verification=result, suggestions=tuple())

        # 3. 修正候補を LLM に提案させる（適用しない）
        logger.info(f"[suggest {model_id}] requesting tool call suggestions ...")
        suggestions = self.tool_based_corrector.suggest_tool_calls(
            cad_model.cad_script,
            result.discrepancies,
            blueprint_image_path=outcome.blueprint_image_path,
            line_views=outcome.line_views,
            shaded_views=outcome.shaded_views,
        )
        logger.info(f"[suggest {model_id}] got {len(suggestions)} suggestions")
        return SuggestCorrectionsResult(
            verification=result,
            suggestions=tuple(suggestions),
        )
