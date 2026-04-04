from pydantic import BaseModel
from typing import Optional


class GenerateResponse(BaseModel):
    model_id: str
    status: str
    stl_path: Optional[str] = None
    error_message: Optional[str] = None


class ModelStatusResponse(BaseModel):
    model_id: str
    status: str
    stl_path: Optional[str] = None
    error_message: Optional[str] = None
