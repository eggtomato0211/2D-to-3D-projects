from pydantic import BaseModel
from typing import Optional


class ParameterResponse(BaseModel):
    name: str
    value: float
    parameter_type: str
    edge_points: list[list[float]] = []


class GenerateResponse(BaseModel):
    model_id: str
    status: str
    stl_path: Optional[str] = None
    error_message: Optional[str] = None
    parameters: list[ParameterResponse] = []


class ModelStatusResponse(BaseModel):
    model_id: str
    status: str
    stl_path: Optional[str] = None
    error_message: Optional[str] = None
    parameters: list[ParameterResponse] = []


class ParameterUpdateRequest(BaseModel):
    parameters: list[ParameterResponse]
