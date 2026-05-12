"""検証 API のレスポンススキーマ。"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel


class DiscrepancySchema(BaseModel):
    feature_type: str
    severity: Literal["critical", "major", "minor"]
    description: str
    expected: str
    actual: str
    confidence: Literal["high", "medium"] = "high"
    location_hint: Optional[str] = None
    dimension_hint: Optional[str] = None


class VerificationResponse(BaseModel):
    is_valid: bool
    critical_count: int
    major_count: int
    minor_count: int
    discrepancies: list[DiscrepancySchema]
    feedback: Optional[str] = None
    raw_response: Optional[str] = None


class VerificationSnapshotSchema(BaseModel):
    iteration: int
    is_valid: bool
    critical_count: int
    major_count: int
    minor_count: int
    outcome: str


class VerifyAndCorrectRequest(BaseModel):
    max_iterations: Optional[int] = None
    cost_budget_usd: Optional[float] = None
    detect_degradation: Optional[bool] = None
    single_fix_per_iteration: Optional[bool] = None
    use_tool_based_correction: Optional[bool] = None  # §10.6
    early_stop_no_improve_k: Optional[int] = None  # §10.6 改善 a


class VerifyAndCorrectResponse(BaseModel):
    final_status: str  # "success" | "max_iterations" | "degradation" | "execute_failed" | "correct_failed" | "budget_exceeded"
    best_iteration: int  # critical 件数最少だった iter 番号（rollback 後の最終状態）
    iterations: list[VerificationSnapshotSchema]
    final: VerificationResponse


# ----- §11.5 Human-in-the-loop -----
class ToolCallSuggestionSchema(BaseModel):
    tool_name: str
    args: dict
    related_discrepancy_index: Optional[int] = None
    rationale: str = ""


class SuggestCorrectionsResponse(BaseModel):
    """検証結果 + 修正候補（適用なし）"""
    verification: VerificationResponse
    suggestions: list[ToolCallSuggestionSchema]


class ToolCallInput(BaseModel):
    """ユーザーが送る承認済み tool call"""
    name: str
    input: dict


class ApplyToolCallsRequest(BaseModel):
    tool_calls: list[ToolCallInput]


class ApplyToolCallsResponse(BaseModel):
    model_id: str
    status: str
    stl_path: Optional[str] = None
    step_path: Optional[str] = None
    error_message: Optional[str] = None
    applied_count: int
