#1. cadexecutorのinterfaceを継承したクラスを作成
from app.domain.interfaces.cad_executor import ICADExecutor
from app.domain.value_objects.cad_script import CadScript
import os
import uuid
import cadquery as cq

class CadQueryExecutor(ICADExecutor):
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
    
    def execute(self, script):
        #出力ディレクトリを作成
        os.makedirs(self.output_dir, exist_ok=True)

        #スクリプトを eec()で実行
        namespace = {}
        exec(script.content, namespace)

        #実行結果を取得
        result = namespace.get("result")
        if result is None:
            raise ValueError("スクリプトの実行結果が見つかりませんでした。")
        
        #結果をファイルに保存
        stl_path = os.path.join(self.output_dir, f"{uuid.uuid4()}.stl")
        cq.exporters.export(result, stl_path)

        return stl_path


        

        