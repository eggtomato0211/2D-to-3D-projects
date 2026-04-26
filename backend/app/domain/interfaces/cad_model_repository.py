from abc import ABC, abstractmethod
from typing import Optional
from ..entities.cad_model import CADModel


class ICADModelRepository(ABC):
    @abstractmethod
    def save(self, cad_model: CADModel) -> None:
        """CADモデルを永続化する（新規・更新どちらでも upsert 挙動）"""
        pass

    @abstractmethod
    def get_by_id(self, cad_model_id: str) -> Optional[CADModel]:
        """CADモデルデータをIDで取得する"""
        pass
