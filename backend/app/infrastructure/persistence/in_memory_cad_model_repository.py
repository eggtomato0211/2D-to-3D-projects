from typing import Dict, Optional
from ...domain.entities.cad_model import CADModel, GenerationStatus
from ...domain.interfaces.cad_model_repository import ICADModelRepository

class InMemoryCADModelRepository(ICADModelRepository):
    def __init__(self):
        self._models: Dict[str, CADModel] = {}
    
    def save(self, cad_model: CADModel) -> None:
        self._models[cad_model.id] = cad_model
    
    def get_by_id(self, cad_model_id: str) -> Optional[CADModel]:
        return self._models.get(cad_model_id)
    
    def update(self, cad_model: CADModel) -> None:
        if cad_model.id not in self._models:
            raise ValueError(f"CADモデルID {cad_model.id} が見つかりません。")
        self._models[cad_model.id] = cad_model

    def update_status(self, cad_model_id: str, status: GenerationStatus) -> None:
        model = self._models.get(cad_model_id)
        if model:
            model.status = status
        else:
            raise ValueError(f"CADモデルID {cad_model_id} が見つかりません。")


