from app.domain.interfaces.cad_executor import ICADExecutor
from app.domain.value_objects.cad_script import CadScript
import ast
import os
import uuid
import cadquery as cq
import shutil


class CadQueryExecutor(ICADExecutor):
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        shutil.rmtree(self.output_dir, ignore_errors=True)
        os.makedirs(self.output_dir, exist_ok=True)

    @staticmethod
    def _validate_script(script: CadScript) -> None:
        """exec() 前の軽量バリデーション。問題があれば ValueError を送出する。"""
        code = script.content

        # 構文チェック
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            raise ValueError(f"構文エラー (行 {e.lineno}): {e.msg}") from e

        # import cadquery の存在確認
        has_cq_import = any(
            (isinstance(node, ast.Import) and any(a.name == "cadquery" for a in node.names))
            or (isinstance(node, ast.ImportFrom) and node.module == "cadquery")
            for node in ast.walk(tree)
        )
        if not has_cq_import:
            raise ValueError("'import cadquery' が見つかりません。スクリプトは import cadquery as cq から始めてください。")

        # result 変数への代入確認
        has_result_assign = any(
            isinstance(node, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "result" for t in node.targets)
            for node in ast.walk(tree)
        )
        if not has_result_assign:
            raise ValueError("'result' 変数への代入が見つかりません。最終形状を result = ... で代入してください。")

    def execute(self, script: CadScript) -> str:
        # プリバリデーション
        self._validate_script(script)

        # スクリプトを exec() で実行
        namespace: dict = {}
        exec(script.content, namespace)

        #実行結果を取得
        result = namespace.get("result")
        if result is None:
            raise ValueError("スクリプトの実行結果が見つかりませんでした。")
        
        #結果をファイルに保存
        filename = f"{uuid.uuid4()}.stl"
        stl_path = os.path.join(self.output_dir, filename)
        cq.exporters.export(result, stl_path)

        return filename


        

        