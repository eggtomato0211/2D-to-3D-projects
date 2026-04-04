from fastapi import APIRouter, HTTPException
from app.presentation.schemas.cad_model_schema import GenerateResponse, ModelStatusResponse
from app.domain.entities.cad_model import CADModel, GenerationStatus
import uuid

router = APIRouter()

# DI で注入される依存性（main.py から設定）
blueprint_repo = None
cad_model_repo = None
generate_cad_usecase = None


def init_router(repo_blueprint, repo_cad_model, usecase_generate_cad):
    """main.py から依存性を注入する"""
    global blueprint_repo, cad_model_repo, generate_cad_usecase
    blueprint_repo = repo_blueprint
    cad_model_repo = repo_cad_model
    generate_cad_usecase = usecase_generate_cad


@router.post("/blueprints/{blueprint_id}/generate", response_model=GenerateResponse)
async def generate_cad(blueprint_id: str):
    """Blueprint から CAD モデルを生成"""
    # Blueprint の存在確認
    blueprint = blueprint_repo.get_by_id(blueprint_id)
    if blueprint is None:
        raise HTTPException(status_code=404, detail="Blueprint not found")

    # CADModel 作成（PENDING）
    model_id = str(uuid.uuid4())
    cad_model = CADModel(
        id=model_id,
        blueprint_id=blueprint_id,
        status=GenerationStatus.PENDING,
    )
    cad_model_repo.save(cad_model)

    # パイプライン実行
    result = generate_cad_usecase.execute(model_id)

    return GenerateResponse(
        model_id=result.id,
        status=result.status.value,
        stl_path=result.stl_path,
        error_message=result.error_message,
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
    )
