from typing import Annotated, Literal, Optional

from pydantic import BaseModel, Field


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


# --- Verification 結果 DTO ---

class DiscrepancyDTO(BaseModel):
    feature_type: str
    severity: Literal["critical", "major", "minor"]
    description: str
    expected: str
    actual: str
    confidence: Literal["high", "medium", "low"] = "high"
    location_hint: Optional[str] = None
    dimension_hint: Optional[str] = None


class VerificationResultDTO(BaseModel):
    is_valid: bool
    critical_count: int
    major_count: int
    minor_count: int
    discrepancies: list[DiscrepancyDTO] = []


class GenerateRequest(BaseModel):
    """生成リクエスト。`model` は使用 VLM の ID。"""
    model: Optional[str] = None


class GenerateResponse(BaseModel):
    model_id: str
    status: str
    clarifications: list[ClarificationResponse] = []
    blueprint_id: Optional[str] = None
    stl_path: Optional[str] = None
    error_message: Optional[str] = None
    parameters: list[ParameterResponse] = []
    verification: Optional[VerificationResultDTO] = None


class ModelStatusResponse(BaseModel):
    model_id: str
    status: str
    stl_path: Optional[str] = None
    error_message: Optional[str] = None
    parameters: list[ParameterResponse] = []
    verification: Optional[VerificationResultDTO] = None


class ParameterUpdateRequest(BaseModel):
    parameters: list[ParameterResponse]


class ConfirmClarificationsRequest(BaseModel):
    responses: dict[str, ClarificationAnswerDTO]
    model: Optional[str] = None


class VerifyAndCorrectRequest(BaseModel):
    model: Optional[str] = None


class EditCadModelRequest(BaseModel):
    instruction: str
    model: Optional[str] = None


# --- VLM モデル一覧 ---

class VlmModelInfo(BaseModel):
    id: str
    label: str
    provider: str
    description: str
    default: bool


class VlmModelListResponse(BaseModel):
    models: list[VlmModelInfo]
    default: str
