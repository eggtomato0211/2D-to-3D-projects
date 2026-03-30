from typing import Dict, Optional
from ...domain.entities.blueprint import Blueprint
from ...domain.interfaces.blueprint_repository import IBlueprintRepository

class InMemoryBluePrintRepository(IBlueprintRepository):
    def __init__(self):
        self._storage: Dict[str, Blueprint] = {}
    
    def save(self, blueprint: Blueprint) -> None:
        self._storage[blueprint.id] = blueprint

    def get_by_id(self, blueprint_id: str) -> Optional[Blueprint]:
        return self._storage.get(blueprint_id)