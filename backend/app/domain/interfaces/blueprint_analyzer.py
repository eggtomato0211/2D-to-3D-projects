from abc import ABC, abstractmethod
from typing import List
from ..entities.blueprint import Blueprint
from ..value_objects.design_step import DesignStep


class IBlueprintAnalyzer(ABC):
    """
    図面画像を解析し、設計手順を抽出するインターフェース（Step 1）
    """

    @abstractmethod
    def analyze(self, blueprint: Blueprint) -> List[DesignStep]:
        """図面データを分析し、設計ステップのリストを返す"""
        pass
