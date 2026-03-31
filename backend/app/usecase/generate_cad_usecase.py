from app.usecase.analyze_blueprint_usecase import AnalyzeBlueprintUseCase
from app.usecase.generate_script_usecase import GenerateScriptUseCase
from app.usecase.execute_script_usecase import ExecuteScriptUseCase



class GenerateCadUseCase:
    def __init__(self, analyze_usecase: AnalyzeBlueprintUseCase, generate_script_usecase: GenerateScriptUseCase, execute_script_usecase: ExecuteScriptUseCase):
        self.analyze_usecase = analyze_usecase
        self.generate_script_usecase = generate_script_usecase
        self.execute_script_usecase = execute_script_usecase
    
    def execute(self, model_id: str):
        #Step 1:図面を解析して設計意図を生成
        design_intent = self.analyze_usecase.execute(model_id)

        #Step 2:設計意図からCadQueryスクリプトを生成
        cad_script = self.generate_script_usecase.execute(model_id, design_intent)

        #Step 3:CadQueryスクリプトを実行してCADモデルを生成
        cad_model = self.execute_script_usecase.execute(model_id, cad_script)

        return cad_model
