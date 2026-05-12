"""§11.5 Human-in-the-loop: ユーザー承認済み tool calls を CADModel に適用。

ユーザーが SuggestCorrectionsUseCase の出力を確認・選択・編集して送ってくる
tool call リストを受け取り、既存スクリプトに append → 再 execute する。
"""
from __future__ import annotations

from loguru import logger

from app.domain.entities.cad_model import CADModel, GenerationStatus
from app.domain.interfaces.cad_executor import ICADExecutor
from app.domain.interfaces.cad_model_repository import ICADModelRepository


class ApplyToolCallsUseCase:
    """ユーザー承認済み tool calls を適用 → execute → CADModel 更新。"""

    def __init__(
        self,
        cad_model_repo: ICADModelRepository,
        cad_executor: ICADExecutor,
        tool_based_corrector,  # AnthropicToolBasedCorrector（apply_tool_calls メソッドだけ使う）
    ) -> None:
        self.cad_model_repo = cad_model_repo
        self.cad_executor = cad_executor
        self.tool_based_corrector = tool_based_corrector

    def execute(self, model_id: str, tool_calls: list[dict]) -> CADModel:
        """承認済み tool calls を適用する。

        Args:
            model_id: 対象 CADModel
            tool_calls: [{name: str, input: dict}, ...] 形式
                       (suggest 出力の `tool_name` / `args` をクライアントで
                        フィルタ・編集して送ってくる想定)

        Returns:
            更新後の CADModel
        """
        cad_model: CADModel = self.cad_model_repo.get_by_id(model_id)
        if cad_model is None:
            raise ValueError(f"CADModel {model_id} が見つかりません")
        if cad_model.cad_script is None:
            raise ValueError(f"CADModel {model_id} に cad_script が無いため適用できません")
        if not tool_calls:
            logger.info(f"[apply {model_id}] no tool calls — no-op")
            return cad_model

        # 1. tool calls を CadQuery に変換 + 既存 script に append
        logger.info(f"[apply {model_id}] applying {len(tool_calls)} tool call(s) ...")
        new_script = self.tool_based_corrector.apply_tool_calls(
            cad_model.cad_script,
            tool_calls,
            dedup_against_existing=False,  # ユーザー承認済みなのでスキップしない
        )

        if new_script.content == cad_model.cad_script.content:
            logger.warning(f"[apply {model_id}] script unchanged after applying tool calls")
            return cad_model

        # 2. 再実行
        cad_model.status = GenerationStatus.EXECUTING
        self.cad_model_repo.save(cad_model)
        try:
            exec_result = self.cad_executor.execute(new_script)
            cad_model.cad_script = new_script
            cad_model.stl_path = exec_result.stl_filename
            cad_model.step_path = exec_result.step_filename
            cad_model.parameters = exec_result.parameters
            cad_model.status = GenerationStatus.SUCCESS
            cad_model.error_message = None
            logger.info(
                f"[apply {model_id}] success: stl={cad_model.stl_path}"
            )
        except Exception as e:
            cad_model.status = GenerationStatus.FAILED
            cad_model.error_message = f"承認済み tool calls の適用後実行に失敗: {e}"
            logger.error(f"[apply {model_id}] execute failed: {e}")
        self.cad_model_repo.save(cad_model)
        return cad_model
