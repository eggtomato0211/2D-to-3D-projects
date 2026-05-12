from __future__ import annotations

import ast
import os
import shutil
import uuid

import cadquery as cq
from loguru import logger

from app.domain.interfaces.cad_executor import ICADExecutor
from app.domain.value_objects.cad_script import CadScript
from app.domain.value_objects.execution_result import ExecutionResult
from app.infrastructure.cad.dimension_extractor import extract_parameters


class CadQueryExecutor(ICADExecutor):
    """CadQuery スクリプトを実行して STL + STEP を書き出す実装。

    STEP は Phase 2 の線画レンダラ入力として必要。書き出し失敗時は STEP のみ
    None で返し、STL 側を活かす（線画レンダリングは諦め、影付きレンダのみ動く）。
    """

    def __init__(self, output_dir: str, *, clear_on_init: bool = False) -> None:
        """uvicorn --reload 中に毎回 /tmp/cad_output を消すと既存 STL も飛ぶので、
        既定はクリアしない。テストや手動運用で明示的にクリアしたい場合のみ True にする。
        """
        self._output_dir = output_dir
        if clear_on_init:
            shutil.rmtree(self._output_dir, ignore_errors=True)
        os.makedirs(self._output_dir, exist_ok=True)

    def execute(self, script: CadScript) -> ExecutionResult:
        self._validate_script(script)

        namespace: dict = {}
        exec(script.content, namespace)  # noqa: S102  - controlled CadQuery script

        shape = namespace.get("result")
        if shape is None:
            raise ValueError("スクリプトの実行結果 (result) が見つかりませんでした。")

        try:
            parameters = extract_parameters(shape)
            logger.info(f"寸法パラメータ抽出完了: {len(parameters)} 件")
        except Exception as e:
            logger.warning(f"寸法パラメータ抽出に失敗（STL 生成は続行）: {e}")
            parameters = []

        base = uuid.uuid4().hex
        stl_filename = f"{base}.stl"
        step_filename: str | None = f"{base}.step"

        cq.exporters.export(shape, os.path.join(self._output_dir, stl_filename))
        try:
            cq.exporters.export(shape, os.path.join(self._output_dir, step_filename))
        except Exception as e:
            logger.warning(f"STEP の書き出しに失敗: {e}")
            step_filename = None

        return ExecutionResult(
            stl_filename=stl_filename,
            parameters=parameters,
            step_filename=step_filename,
        )

    # ---- internal ----
    @staticmethod
    def _validate_script(script: CadScript) -> None:
        code = script.content
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            raise ValueError(f"構文エラー (行 {e.lineno}): {e.msg}") from e

        has_cq_import = any(
            (isinstance(node, ast.Import) and any(a.name == "cadquery" for a in node.names))
            or (isinstance(node, ast.ImportFrom) and node.module == "cadquery")
            for node in ast.walk(tree)
        )
        if not has_cq_import:
            raise ValueError(
                "'import cadquery' が見つかりません。"
                "スクリプトは import cadquery as cq から始めてください。"
            )

        has_result_assign = any(
            isinstance(node, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "result" for t in node.targets)
            for node in ast.walk(tree)
        )
        if not has_result_assign:
            raise ValueError(
                "'result' 変数への代入が見つかりません。"
                "最終形状を result = ... で代入してください。"
            )
