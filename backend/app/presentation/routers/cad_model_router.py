"""CAD モデル生成・検証・パラメータ更新を司るルーター。

VLM モデル ID はリクエストの body / query で受け取り、PipelineFactory が
リクエストごとに usecase をビルドする。
"""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.domain.entities.cad_model import CADModel, GenerationStatus
from app.domain.interfaces.blueprint_repository import IBlueprintRepository
from app.domain.interfaces.cad_model_repository import ICADModelRepository
from app.domain.value_objects.clarification import (
    ClarificationAnswer,
    CustomAnswer,
    NoAnswer,
    YesAnswer,
)
from app.domain.value_objects.discrepancy import Discrepancy
from app.domain.value_objects.model_parameter import ModelParameter, ParameterType
from app.domain.value_objects.verification import VerificationResult
from app.infrastructure.vlm import model_factory
from app.presentation.pipeline_factory import PipelineFactory
from app.presentation.schemas.cad_model_schema import (
    ClarificationResponse,
    ConfirmClarificationsRequest,
    CustomAnswerDTO,
    DiscrepancyDTO,
    GenerateRequest,
    GenerateResponse,
    ModelStatusResponse,
    NoAnswerDTO,
    ParameterResponse,
    ParameterUpdateRequest,
    VerifyAndCorrectRequest,
    VerificationResultDTO,
    VlmModelInfo,
    VlmModelListResponse,
    YesAnswerDTO,
)

router = APIRouter()

# DI 注入用（main.py から init_router で設定）
_blueprint_repo: Optional[IBlueprintRepository] = None
_cad_model_repo: Optional[ICADModelRepository] = None
_pipeline_factory: Optional[PipelineFactory] = None


def init_router(
    blueprint_repo: IBlueprintRepository,
    cad_model_repo: ICADModelRepository,
    pipeline_factory: PipelineFactory,
) -> None:
    global _blueprint_repo, _cad_model_repo, _pipeline_factory
    _blueprint_repo = blueprint_repo
    _cad_model_repo = cad_model_repo
    _pipeline_factory = pipeline_factory


# ---- VLM モデル一覧 ----

@router.get("/vlm-models", response_model=VlmModelListResponse)
async def list_vlm_models() -> VlmModelListResponse:
    """UI から選択可能な VLM モデルの一覧を返す。"""
    return VlmModelListResponse(
        models=[VlmModelInfo(**m) for m in model_factory.SUPPORTED_MODELS],
        default=model_factory.DEFAULT_MODEL,
    )


# ---- 生成 ----

@router.post("/blueprints/{blueprint_id}/generate", response_model=GenerateResponse)
async def generate_cad(blueprint_id: str, body: Optional[GenerateRequest] = None):
    """Blueprint から CAD モデルを生成する。

    確認事項がある場合は status="needs_clarification" でユーザー回答待ち。
    """
    assert _blueprint_repo is not None and _cad_model_repo is not None
    assert _pipeline_factory is not None

    if _blueprint_repo.get_by_id(blueprint_id) is None:
        raise HTTPException(status_code=404, detail="Blueprint not found")

    vlm_model_id = _pipeline_factory.resolve_model(body.model if body else None)
    model_id = str(uuid.uuid4())
    cad_model = CADModel(
        id=model_id, blueprint_id=blueprint_id,
        status=GenerationStatus.PENDING,
        model_provider_id=vlm_model_id,
    )
    _cad_model_repo.save(cad_model)

    pipeline = _pipeline_factory.build_generate_cad(vlm_model_id)
    result = pipeline.execute(model_id)

    if result.clarifications and not result.clarifications_confirmed:
        return GenerateResponse(
            model_id=result.id,
            status="needs_clarification",
            clarifications=_to_clarification_response(result.clarifications),
            blueprint_id=blueprint_id,
        )
    return _to_generate_response(result)


@router.post(
    "/blueprints/{blueprint_id}/confirm-clarifications",
    response_model=GenerateResponse,
)
async def confirm_clarifications(
    blueprint_id: str,
    model_id: str = Query(...),
    body: ConfirmClarificationsRequest = None,
):
    """ユーザーが確認事項に回答 → Step 2 & 3 を実行する。"""
    assert _cad_model_repo is not None and _pipeline_factory is not None
    if body is None:
        raise HTTPException(status_code=400, detail="Request body required")

    cad_model = _cad_model_repo.get_by_id(model_id)
    if cad_model is None:
        raise HTTPException(status_code=404, detail="Model not found")

    responses = {k: _dto_to_answer(dto) for k, dto in body.responses.items()}
    vlm_model_id = _pipeline_factory.resolve_model(
        body.model or cad_model.model_provider_id
    )
    pipeline = _pipeline_factory.build_confirm_clarifications(vlm_model_id)
    result = pipeline.execute(model_id, responses)
    return _to_generate_response(result)


# ---- 検証 + 修正ループ ----

@router.post(
    "/models/{model_id}/verify-and-correct", response_model=ModelStatusResponse
)
async def verify_and_correct(
    model_id: str, body: Optional[VerifyAndCorrectRequest] = None,
):
    """検証 → 修正ループを実行して best 状態に収束させる。"""
    assert _cad_model_repo is not None and _pipeline_factory is not None
    cad_model = _cad_model_repo.get_by_id(model_id)
    if cad_model is None:
        raise HTTPException(status_code=404, detail="Model not found")

    vlm_model_id = _pipeline_factory.resolve_model(
        (body.model if body else None) or cad_model.model_provider_id
    )
    pipeline = _pipeline_factory.build_verify_and_correct(vlm_model_id)
    result = pipeline.execute(model_id)
    return _to_status_response(result)


# ---- 既存: モデル取得・パラメータ更新 ----

@router.get("/models/{model_id}", response_model=ModelStatusResponse)
async def get_model_status(model_id: str):
    assert _cad_model_repo is not None
    cad_model = _cad_model_repo.get_by_id(model_id)
    if cad_model is None:
        raise HTTPException(status_code=404, detail="Model not found")
    return _to_status_response(cad_model)


@router.put("/models/{model_id}/parameters", response_model=ModelStatusResponse)
async def update_parameters(model_id: str, body: ParameterUpdateRequest):
    assert _cad_model_repo is not None and _pipeline_factory is not None
    cad_model = _cad_model_repo.get_by_id(model_id)
    if cad_model is None:
        raise HTTPException(status_code=404, detail="Model not found")

    new_parameters = [
        ModelParameter(
            name=p.name, value=p.value,
            parameter_type=ParameterType(p.parameter_type),
        )
        for p in body.parameters
    ]
    pipeline = _pipeline_factory.build_update_parameters(cad_model.model_provider_id)
    result = pipeline.execute(model_id, new_parameters)
    return _to_status_response(result)


# ---- DTO ↔ ドメインの変換 ----

def _to_parameter_response(model: CADModel) -> list[ParameterResponse]:
    return [
        ParameterResponse(
            name=p.name, value=p.value,
            parameter_type=p.parameter_type.value,
            edge_points=p.edge_points,
        )
        for p in model.parameters
    ]


def _answer_to_dto(answer: ClarificationAnswer | None):
    match answer:
        case None:
            return None
        case YesAnswer():
            return YesAnswerDTO()
        case NoAnswer():
            return NoAnswerDTO()
        case CustomAnswer(text=text):
            return CustomAnswerDTO(text=text)


def _dto_to_answer(dto) -> ClarificationAnswer:
    match dto:
        case YesAnswerDTO():
            return YesAnswer()
        case NoAnswerDTO():
            return NoAnswer()
        case CustomAnswerDTO(text=text):
            return CustomAnswer(text=text)
    raise ValueError(f"Unknown clarification answer DTO: {dto!r}")


def _to_clarification_response(clarifications) -> list[ClarificationResponse]:
    return [
        ClarificationResponse(
            id=c.id, question=c.question,
            candidates=[_answer_to_dto(cand) for cand in c.candidates],
        )
        for c in clarifications
    ]


def _to_discrepancy_dto(d: Discrepancy) -> DiscrepancyDTO:
    return DiscrepancyDTO(
        feature_type=d.feature_type,
        severity=d.severity,
        description=d.description,
        expected=d.expected,
        actual=d.actual,
        confidence=d.confidence,
        location_hint=d.location_hint,
        dimension_hint=d.dimension_hint,
    )


def _to_verification_dto(r: VerificationResult | None) -> VerificationResultDTO | None:
    if r is None:
        return None
    return VerificationResultDTO(
        is_valid=r.is_valid,
        critical_count=r.critical_count(),
        major_count=r.major_count(),
        minor_count=r.minor_count(),
        discrepancies=[_to_discrepancy_dto(d) for d in r.discrepancies],
    )


def _to_generate_response(model: CADModel) -> GenerateResponse:
    return GenerateResponse(
        model_id=model.id,
        status=model.status.value,
        clarifications=_to_clarification_response(model.clarifications),
        stl_path=model.stl_path,
        error_message=model.error_message,
        parameters=_to_parameter_response(model),
        verification=_to_verification_dto(model.verification_result),
    )


def _to_status_response(model: CADModel) -> ModelStatusResponse:
    return ModelStatusResponse(
        model_id=model.id,
        status=model.status.value,
        stl_path=model.stl_path,
        error_message=model.error_message,
        parameters=_to_parameter_response(model),
        verification=_to_verification_dto(model.verification_result),
    )
