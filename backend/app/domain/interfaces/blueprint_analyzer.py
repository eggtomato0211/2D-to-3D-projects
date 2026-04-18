from abc import ABC, abstractmethod
from ..entities.blueprint import Blueprint
from ..entities.design_intent import DesignIntent


class IBlueprintAnalyzer(ABC):
    """
    図面画像を解析し、設計意図（手順と確認事項）を抽出するインターフェース（Step 1）
    """

    @abstractmethod
    def analyze(self, blueprint: Blueprint) -> DesignIntent:
        """図面データを分析し、設計意図（DesignIntent）を返す"""
        pass
