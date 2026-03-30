import uuid
from typing import List
from ..domain.entities.blueprint import Blueprint
from ..domain.entities.cad_model import CADModel, GenerationStatus
from ..domain.entities.design_intent import DesignIntent
from ..domain.interfaces.blueprint_repository import IBlueprintRepository
from ..domain.interfaces.cad_model_repository import ICADModelRepository
from ..domain.interfaces.vlm_service import IVlmService

