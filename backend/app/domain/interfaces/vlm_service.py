from abc import ABC, abstractmethod
from typing import List
from ..entities.blueprint import Blueprint
from ..entities.cad_model import CADModel
from ..entities.design_intent import DesignIntent
from ..value_objects.design_step import DesignStep
from ..value_objects.cad_script import CadScript
from ..value_objects.verification import VerificationResult

class IVlmService(ABC):
    """
    VLM(AI)との通信を抽象化するインターフェース
    """
    @abstractmethod
    def analyze_blueprint(self, blueprint: Blueprint) -> List[DesignStep]:
        """図面データを分析し、設計ステップのリストを返すメソッド"""
        pass

    @abstractmethod
    def generate_script(self, design_intent: DesignIntent) -> CadScript:
        """設計意図から CadQuery スクリプトを生成"""
        pass

    @abstractmethod
    def verify_cad_model(self, cad_model: CADModel) -> VerificationResult:
        """元の図面と、生成されたCADモデル（のレンダリング画像など）を比較し、
        設計通りか、修正が必要かを判定する。"""
        pass


