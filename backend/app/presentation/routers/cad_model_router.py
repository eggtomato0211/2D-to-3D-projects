from fastapi import APIRouter, HTTPException, Query
from app.presentation.schemas.cad_model_schema import (
    GenerateResponse,
    ModelStatusResponse,
    ParameterResponse,
    ParameterUpdateRequest,
    ClarificationResponse,
    ConfirmClarificationsRequest,
    YesAnswerDTO,
    NoAnswerDTO,
    CustomAnswerDTO,
)
from app.domain.entities.cad_model import CADModel, GenerationStatus
from app.domain.value_objects.model_parameter import ModelParameter, ParameterType
from app.domain.value_objects.clarification import (
    ClarificationAnswer,
    YesAnswer,
    NoAnswer,
    CustomAnswer,
)
import uuid

router = APIRouter()

# DI で注入される依存性（main.py から設定）
blueprint_repo = None
cad_model_repo = None
generate_cad_usecase = None
confirm_clarifications_usecase = None
update_parameters_usecase = None


def init_router(repo_blueprint, repo_cad_model, usecase_generate_cad, usecase_confirm_clarifications=None, usecase_update_parameters=None):
    """main.py から依存性を注入する"""
    global blueprint_repo, cad_model_repo, generate_cad_usecase, confirm_clarifications_usecase, update_parameters_usecase
    blueprint_repo = repo_blueprint
    cad_model_repo = repo_cad_model
    generate_cad_usecase = usecase_generate_cad
    confirm_clarifications_usecase = usecase_confirm_clarifications
    update_parameters_usecase = usecase_update_parameters


def _to_parameter_response(model: CADModel) -> list[ParameterResponse]:
    return [
        ParameterResponse(
            name=p.name,
            value=p.value,
            parameter_type=p.parameter_type.value,
            edge_points=p.edge_points,
        )
        for p in model.parameters
    ]


def _answer_to_dto(answer: ClarificationAnswer | None):
    """ドメインの ClarificationAnswer を Pydantic DTO に変換する"""
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
    """Pydantic DTO をドメインの ClarificationAnswer に変換する"""
    match dto:
        case YesAnswerDTO():
            return YesAnswer()
        case NoAnswerDTO():
            return NoAnswer()
        case CustomAnswerDTO(text=text):
            return CustomAnswer(text=text)
        case _:
            raise ValueError(f"Unknown clarification answer DTO: {dto!r}")


def _to_clarification_response(clarifications) -> list[ClarificationResponse]:
    return [
        ClarificationResponse(
            id=c.id,
            question=c.question,
            candidates=[_answer_to_dto(cand) for cand in c.candidates],
            suggested_answer=_answer_to_dto(c.suggested_answer),
        )
        for c in clarifications
    ]


@router.post("/blueprints/{blueprint_id}/generate", response_model=GenerateResponse)
async def generate_cad(blueprint_id: str):
    """Blueprint から CAD モデルを生成

    確認事項（clarifications）がある場合は、status="needs_clarification" で返す。
    """
    blueprint = blueprint_repo.get_by_id(blueprint_id)
    if blueprint is None:
        raise HTTPException(status_code=404, detail="Blueprint not found")

    model_id = str(uuid.uuid4())
    cad_model = CADModel(
        id=model_id,
        blueprint_id=blueprint_id,
        status=GenerationStatus.PENDING,
    )
    cad_model_repo.save(cad_model)

    result = generate_cad_usecase.execute(model_id)

    # 確認事項がある場合（ユーザー確認待機中）
    if result.clarifications and not result.clarifications_confirmed:
        return GenerateResponse(
            model_id=result.id,
            status="needs_clarification",
            clarifications=_to_clarification_response(result.clarifications),
            blueprint_id=blueprint_id,
            stl_path=None,
            error_message=None,
            parameters=[],
        )

    # 通常の成功/失敗レスポンス
    return GenerateResponse(
        model_id=result.id,
        status=result.status.value,
        clarifications=[],
        stl_path=result.stl_path,
        error_message=result.error_message,
        parameters=_to_parameter_response(result),
    )


@router.post("/blueprints/{blueprint_id}/confirm-clarifications", response_model=GenerateResponse)
async def confirm_clarifications(
    blueprint_id: str,
    model_id: str = Query(...),
    body: ConfirmClarificationsRequest = None,
):
    """ユーザーが確認事項に回答したら、Step 2 & 3 を実行する"""
    if confirm_clarifications_usecase is None:
        raise HTTPException(status_code=501, detail="Clarification confirmation not configured")

    cad_model = cad_model_repo.get_by_id(model_id)
    if cad_model is None:
        raise HTTPException(status_code=404, detail="Model not found")

    if body is None:
        raise HTTPException(status_code=400, detail="Request body required")

    domain_responses = {
        key: _dto_to_answer(dto) for key, dto in body.responses.items()
    }
    result = confirm_clarifications_usecase.execute(model_id, domain_responses)

    return GenerateResponse(
        model_id=result.id,
        status=result.status.value,
        clarifications=_to_clarification_response(result.clarifications),
        stl_path=result.stl_path,
        error_message=result.error_message,
        parameters=_to_parameter_response(result),
    )


@router.get("/models/{model_id}", response_model=ModelStatusResponse)
async def get_model_status(model_id: str):
    """生成結果を取得"""
    cad_model = cad_model_repo.get_by_id(model_id)
    if cad_model is None:
        raise HTTPException(status_code=404, detail="Model not found")

    return ModelStatusResponse(
        model_id=cad_model.id,
        status=cad_model.status.value,
        stl_path=cad_model.stl_path,
        error_message=cad_model.error_message,
        parameters=_to_parameter_response(cad_model),
    )


@router.put("/models/{model_id}/parameters", response_model=ModelStatusResponse)
async def update_parameters(model_id: str, body: ParameterUpdateRequest):
    """パラメータを変更してモデルを再生成"""
    if update_parameters_usecase is None:
        raise HTTPException(status_code=501, detail="Parameter update not configured")

    cad_model = cad_model_repo.get_by_id(model_id)
    if cad_model is None:
        raise HTTPException(status_code=404, detail="Model not found")

    new_parameters = [
        ModelParameter(
            name=p.name,
            value=p.value,
            parameter_type=ParameterType(p.parameter_type),
        )
        for p in body.parameters
    ]

    result = update_parameters_usecase.execute(model_id, new_parameters)

    return ModelStatusResponse(
        model_id=result.id,
        status=result.status.value,
        stl_path=result.stl_path,
        error_message=result.error_message,
        parameters=_to_parameter_response(result),
    )
