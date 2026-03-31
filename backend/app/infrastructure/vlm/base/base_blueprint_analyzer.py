from app.domain.entities.blueprint import Blueprint
from app.domain.value_objects.design_step import DesignStep
from app.domain.interfaces.blueprint_analyzer import IBlueprintAnalyzer
from abc import abstractmethod
import base64
import json
from typing import List

class BaseBlueprintAnalyzer(IBlueprintAnalyzer):

    def _encode_image(self, file_path: str) -> str:
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    
    def _parse_response(self, content: str) -> List[DesignStep]:
        data = json.loads(content)
        return [
            DesignStep(
                step_number=step["step_number"],
                instruction=step["instruction"],
            )
            for step in data["steps"]
        ]
    
    def _build_system_prompt(self) -> str:
        return """あなたは優秀なCADエンジニアです。与えられた2D図面画像を分析し、CadQueryで3Dモデルを作成するための手順を自然言語でステップバイステップに記述してください。

以下のJSON形式で出力してください:
{
  "steps": [
    {"step_number": 1, "instruction": "手順の説明"},
    {"step_number": 2, "instruction": "手順の説明"}
  ]
}

注意事項:
- instruction には具体的な寸法（mm）、形状、位置関係を含めること
- 各ステップは1つのモデリング操作に対応させること
- step_number は 1 から始まる連番"""
    
    def analyze(self, blueprint: Blueprint) -> List[DesignStep]:
        image_data = self._encode_image(blueprint.file_path)
        content = self._call_api(image_data)
        return self._parse_response(content)

    @abstractmethod
    def _call_api(self, image_data: str) -> str:
        """LLM API を呼び出し、JSON 文字列を返す"""
        pass
        
