from typing import Dict, Optional
from ...domain.entities.cad_model import CADModel
from ...domain.interfaces.cad_model_repository import ICADModelRepository


class InMemoryCADModelRepository(ICADModelRepository):
    def __init__(self):
        self._models: Dict[str, CADModel] = {}

    def save(self, cad_model: CADModel) -> None:
        self._models[cad_model.id] = cad_model

    def get_by_id(self, cad_model_id: str) -> Optional[CADModel]:
        return self._models.get(cad_model_id)
