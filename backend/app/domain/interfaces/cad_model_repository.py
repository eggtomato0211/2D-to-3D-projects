from abc import ABC, abstractmethod
from typing import Optional
from ..entities.cad_model import CADModel, GenerationStatus

class ICADModelRepository(ABC):
    @abstractmethod
    def save(self, cad_model: CADModel) -> None:
        """CADモデルデータを保存するためのメソッド"""
        pass
    
    @abstractmethod
    def get_by_id(self, cad_model_id: str) -> Optional[CADModel]:
        """CADモデルデータをIDで取得するためのメソッド"""
        pass
    
    @abstractmethod
    def update_status(self, cad_model_id: str, status: GenerationStatus) -> None:
        """CADモデルのステータスを更新するためのメソッド"""
        pass
