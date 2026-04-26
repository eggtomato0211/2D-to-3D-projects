from abc import ABC, abstractmethod
from ..entities.blueprint import Blueprint
from ..value_objects.design_step import DesignStep
from ..value_objects.clarification import Clarification


class IBlueprintAnalyzer(ABC):
    """
    図面画像を解析し、設計手順と確認事項を抽出するインターフェース（Step 1）
    """

    @abstractmethod
    def analyze(self, blueprint: Blueprint) -> tuple[list[DesignStep], list[Clarification]]:
        """図面データを分析し、(設計手順, 確認事項) のタプルを返す"""
        pass
