from fastapi import APIRouter, UploadFile, File
from app.presentation.schemas.blueprint_schema import UploadResponse
from app.domain.entities.blueprint import Blueprint
import uuid
import os

router = APIRouter()

# DI で注入される依存性（main.py から設定）
blueprint_repo = None

UPLOAD_DIR = "/tmp/blueprints"


def init_router(repo_blueprint):
    """main.py から依存性を注入する"""
    global blueprint_repo
    blueprint_repo = repo_blueprint


@router.post("/blueprints/upload", response_model=UploadResponse)
async def upload_blueprint(file: UploadFile = File(...)):
    """図面をアップロードして Blueprint を作成"""
    blueprint_id = str(uuid.uuid4())

    # ファイル保存
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, f"{blueprint_id}_{file.filename}")
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # Blueprint エンティティ作成・保存
    blueprint = Blueprint(
        id=blueprint_id,
        file_path=file_path,
        file_name=file.filename,
        content_type=file.content_type or "image/png",
    )
    blueprint_repo.save(blueprint)

    return UploadResponse(blueprint_id=blueprint_id)
