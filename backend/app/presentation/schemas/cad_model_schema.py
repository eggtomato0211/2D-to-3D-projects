from pydantic import BaseModel, Field
from typing import Annotated, Literal, Optional


class ParameterResponse(BaseModel):
    name: str
    value: float
    parameter_type: str
    edge_points: list[list[float]] = []


# --- Clarification 回答の discriminated union DTO ---

class YesAnswerDTO(BaseModel):
    kind: Literal["yes"] = "yes"


class NoAnswerDTO(BaseModel):
    kind: Literal["no"] = "no"


class CustomAnswerDTO(BaseModel):
    kind: Literal["custom"] = "custom"
    text: str


ClarificationAnswerDTO = Annotated[
    YesAnswerDTO | NoAnswerDTO | CustomAnswerDTO,
    Field(discriminator="kind"),
]


class ClarificationResponse(BaseModel):
    id: str
    question: str
    candidates: list[ClarificationAnswerDTO] = []


class GenerateResponse(BaseModel):
    model_id: str
    status: str  # "needs_clarification" | "pending" | "analyzing" | ... | "success" | "failed"
    clarifications: list[ClarificationResponse] = []
    blueprint_id: Optional[str] = None  # clarifications endpoint 用
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


class ConfirmClarificationsRequest(BaseModel):
    responses: dict[str, ClarificationAnswerDTO]
