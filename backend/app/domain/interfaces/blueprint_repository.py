from abc import ABC, abstractmethod
from typing import Optional
from ..entities.blueprint import Blueprint

class IBlueprintRepository(ABC):
    @abstractmethod
    def save(self, blueprint: Blueprint) -> None:
        """図面データを保存するためのメソッド"""
        pass
    
    @abstractmethod
    def get_by_id(self, blueprint_id: str) -> Optional[Blueprint]:
        """図面データをIDで取得するためのメソッド"""
        pass
        