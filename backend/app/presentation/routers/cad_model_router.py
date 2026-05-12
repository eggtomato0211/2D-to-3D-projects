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
from app.presentation.schemas.verification_schema import (
    ApplyToolCallsRequest,
    ApplyToolCallsResponse,
    DiscrepancySchema,
    SuggestCorrectionsResponse,
    ToolCallSuggestionSchema,
    VerificationResponse,
    VerificationSnapshotSchema,
    VerifyAndCorrectRequest,
    VerifyAndCorrectResponse,
)
from app.domain.value_objects.loop_config import LoopConfig
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
verify_cad_model_usecase = None
verify_and_correct_usecase = None
suggest_corrections_usecase = None
apply_tool_calls_usecase = None


def init_router(
    repo_blueprint,
    repo_cad_model,
    usecase_generate_cad,
    usecase_confirm_clarifications=None,
    usecase_update_parameters=None,
    usecase_verify_cad_model=None,
    usecase_verify_and_correct=None,
    usecase_suggest_corrections=None,
    usecase_apply_tool_calls=None,
):
    """main.py から依存性を注入する"""
    global blueprint_repo, cad_model_repo, generate_cad_usecase
    global confirm_clarifications_usecase, update_parameters_usecase
    global verify_cad_model_usecase, verify_and_correct_usecase
    global suggest_corrections_usecase, apply_tool_calls_usecase
    blueprint_repo = repo_blueprint
    cad_model_repo = repo_cad_model
    generate_cad_usecase = usecase_generate_cad
    confirm_clarifications_usecase = usecase_confirm_clarifications
    update_parameters_usecase = usecase_update_parameters
    verify_cad_model_usecase = usecase_verify_cad_model
    verify_and_correct_usecase = usecase_verify_and_correct
    suggest_corrections_usecase = usecase_suggest_corrections
    apply_tool_calls_usecase = usecase_apply_tool_calls


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


@router.post("/models/{model_id}/verify", response_model=VerificationResponse)
async def verify_model(model_id: str):
    """生成済みの CAD モデルを元 Blueprint と比較検証する（Phase 2-α/γ）。

    フロー: shaded 4 視点レンダ + line 4 視点レンダ → VLM で比較 → Discrepancy 一覧返却
    """
    if verify_cad_model_usecase is None:
        raise HTTPException(status_code=501, detail="Verification not configured")
    cad_model = cad_model_repo.get_by_id(model_id)
    if cad_model is None:
        raise HTTPException(status_code=404, detail="Model not found")

    try:
        outcome = verify_cad_model_usecase.execute(model_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    result = outcome.result
    return VerificationResponse(
        is_valid=result.is_valid,
        critical_count=result.critical_count(),
        major_count=result.major_count(),
        minor_count=result.minor_count(),
        discrepancies=[
            DiscrepancySchema(
                feature_type=d.feature_type,
                severity=d.severity,
                description=d.description,
                expected=d.expected,
                actual=d.actual,
                confidence=d.confidence,
                location_hint=d.location_hint,
                dimension_hint=d.dimension_hint,
            )
            for d in result.discrepancies
        ],
        feedback=result.feedback,
        raw_response=result.raw_response,
    )


@router.post(
    "/models/{model_id}/verify-and-correct",
    response_model=VerifyAndCorrectResponse,
)
async def verify_and_correct(model_id: str, body: VerifyAndCorrectRequest | None = None):
    """検証 → 修正 → 再実行 → 再検証 を上限まで反復する（Phase 2-δ ループ）。"""
    if verify_and_correct_usecase is None:
        raise HTTPException(status_code=501, detail="Verify-and-correct not configured")
    cad_model = cad_model_repo.get_by_id(model_id)
    if cad_model is None:
        raise HTTPException(status_code=404, detail="Model not found")

    # body が来ていれば LoopConfig を上書き、無ければ usecase 既定値
    base_cfg = verify_and_correct_usecase.config
    if body is not None:
        cfg = LoopConfig(
            max_iterations=body.max_iterations or base_cfg.max_iterations,
            cost_budget_usd=body.cost_budget_usd or base_cfg.cost_budget_usd,
            detect_degradation=(
                body.detect_degradation
                if body.detect_degradation is not None
                else base_cfg.detect_degradation
            ),
            cost_per_verify_usd=base_cfg.cost_per_verify_usd,
            cost_per_correct_usd=base_cfg.cost_per_correct_usd,
            single_fix_per_iteration=(
                body.single_fix_per_iteration
                if body.single_fix_per_iteration is not None
                else base_cfg.single_fix_per_iteration
            ),
            use_tool_based_correction=(
                body.use_tool_based_correction
                if body.use_tool_based_correction is not None
                else base_cfg.use_tool_based_correction
            ),
            early_stop_no_improve_k=(
                body.early_stop_no_improve_k
                if body.early_stop_no_improve_k is not None
                else base_cfg.early_stop_no_improve_k
            ),
        )
    else:
        cfg = base_cfg

    try:
        cad_model, final_result, outcome, best_iteration = (
            verify_and_correct_usecase.execute(model_id, cfg)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return VerifyAndCorrectResponse(
        final_status=outcome,
        best_iteration=best_iteration,
        iterations=[
            VerificationSnapshotSchema(
                iteration=s.iteration,
                is_valid=s.is_valid,
                critical_count=s.critical_count,
                major_count=s.major_count,
                minor_count=s.minor_count,
                outcome=s.outcome,
            )
            for s in cad_model.verification_history
        ],
        final=VerificationResponse(
            is_valid=final_result.is_valid,
            critical_count=final_result.critical_count(),
            major_count=final_result.major_count(),
            minor_count=final_result.minor_count(),
            discrepancies=[
                DiscrepancySchema(
                    feature_type=d.feature_type,
                    severity=d.severity,
                    description=d.description,
                    expected=d.expected,
                    actual=d.actual,
                    confidence=d.confidence,
                    location_hint=d.location_hint,
                    dimension_hint=d.dimension_hint,
                )
                for d in final_result.discrepancies
            ],
            feedback=final_result.feedback,
            raw_response=final_result.raw_response,
        ),
    )


# ============================================================
# §11.5 Human-in-the-loop endpoints
# ============================================================
@router.post(
    "/models/{model_id}/suggest-corrections",
    response_model=SuggestCorrectionsResponse,
)
async def suggest_corrections(model_id: str):
    """検証 + 修正候補（tool calls）を返す。適用は行わない。

    Human-in-the-loop UI から呼び出し、ユーザーが結果を確認・選択して
    `apply-tool-calls` で承認済みのものだけを適用する流れを想定。
    """
    if suggest_corrections_usecase is None:
        raise HTTPException(status_code=501, detail="Suggest corrections not configured")
    cad_model = cad_model_repo.get_by_id(model_id)
    if cad_model is None:
        raise HTTPException(status_code=404, detail="Model not found")

    try:
        result = suggest_corrections_usecase.execute(model_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    v = result.verification
    return SuggestCorrectionsResponse(
        verification=VerificationResponse(
            is_valid=v.is_valid,
            critical_count=v.critical_count(),
            major_count=v.major_count(),
            minor_count=v.minor_count(),
            discrepancies=[
                DiscrepancySchema(
                    feature_type=d.feature_type,
                    severity=d.severity,
                    description=d.description,
                    expected=d.expected,
                    actual=d.actual,
                    confidence=d.confidence,
                    location_hint=d.location_hint,
                    dimension_hint=d.dimension_hint,
                )
                for d in v.discrepancies
            ],
            feedback=v.feedback,
            raw_response=v.raw_response,
        ),
        suggestions=[
            ToolCallSuggestionSchema(
                tool_name=s.tool_name,
                args=s.args,
                related_discrepancy_index=s.related_discrepancy_index,
                rationale=s.rationale,
            )
            for s in result.suggestions
        ],
    )


@router.post(
    "/models/{model_id}/apply-tool-calls",
    response_model=ApplyToolCallsResponse,
)
async def apply_tool_calls(model_id: str, body: ApplyToolCallsRequest):
    """ユーザー承認済みの tool calls を CADModel に適用 + 再実行。

    `suggest-corrections` の出力をユーザーが UI で確認・選択・編集した結果を
    {tool_calls: [{name, input}, ...]} で送信する。
    """
    if apply_tool_calls_usecase is None:
        raise HTTPException(status_code=501, detail="Apply tool calls not configured")
    cad_model = cad_model_repo.get_by_id(model_id)
    if cad_model is None:
        raise HTTPException(status_code=404, detail="Model not found")

    raw_calls = [{"name": tc.name, "input": tc.input} for tc in body.tool_calls]
    try:
        updated = apply_tool_calls_usecase.execute(model_id, raw_calls)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return ApplyToolCallsResponse(
        model_id=updated.id,
        status=updated.status.value,
        stl_path=updated.stl_path,
        step_path=updated.step_path,
        error_message=updated.error_message,
        applied_count=len(raw_calls),
    )
