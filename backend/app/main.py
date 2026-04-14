from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

# Infrastructure
from app.infrastructure.persistence.in_memory_blueprint_repository import InMemoryBlueprintRepository
from app.infrastructure.persistence.in_memory_cad_model_repository import InMemoryCADModelRepository
from app.infrastructure.vlm.gemini.gemini_blueprint_analyzer import GeminiBlueprintAnalyzer
from app.infrastructure.vlm.openai.openai_o3_script_generator import OpenAIO3ScriptGenerator
from app.infrastructure.cad.cadquery_executor import CadQueryExecutor

# UseCase
from app.usecase.analyze_blueprint_usecase import AnalyzeBlueprintUseCase
from app.usecase.generate_script_usecase import GenerateScriptUseCase
from app.usecase.execute_script_usecase import ExecuteScriptUseCase
from app.usecase.generate_cad_usecase import GenerateCadUseCase
from app.usecase.update_parameters_usecase import UpdateParametersUseCase

# Presentation
from app.presentation.routers.blueprint_router import router as blueprint_router
from app.presentation.routers.blueprint_router import init_router as init_blueprint_router
from app.presentation.routers.cad_model_router import router as cad_model_router
from app.presentation.routers.cad_model_router import init_router as init_cad_model_router

app = FastAPI(title="Blueprint to CAD API")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# STLファイル配信用の静的ファイルマウント
cad_output_dir = "/tmp/cad_output"
os.makedirs(cad_output_dir, exist_ok=True)
app.mount("/files", StaticFiles(directory=cad_output_dir), name="files")

# --- DI 組み立て ---

# リポジトリ
blueprint_repo = InMemoryBlueprintRepository()
cad_model_repo = InMemoryCADModelRepository()

# Infrastructure（外部サービス）
blueprint_analyzer = GeminiBlueprintAnalyzer(
    api_key=os.getenv("GEMINI_API_KEY"),
)
script_generator = OpenAIO3ScriptGenerator(
    api_key=os.getenv("OPENAI_API_KEY"),
)
cad_executor = CadQueryExecutor(output_dir="/tmp/cad_output")

# UseCase
analyze_uc = AnalyzeBlueprintUseCase(blueprint_repo, cad_model_repo, blueprint_analyzer)
generate_script_uc = GenerateScriptUseCase(cad_model_repo, script_generator)
execute_script_uc = ExecuteScriptUseCase(cad_model_repo, cad_executor)
generate_cad_uc = GenerateCadUseCase(analyze_uc, generate_script_uc, execute_script_uc, script_generator)
update_params_uc = UpdateParametersUseCase(cad_model_repo, cad_executor, script_generator)

# ルーターに依存性を注入
init_blueprint_router(blueprint_repo)
init_cad_model_router(blueprint_repo, cad_model_repo, generate_cad_uc, update_params_uc)

# ルーター登録
app.include_router(blueprint_router)
app.include_router(cad_model_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


# --- テスト用: LLM を経由せず固定スクリプトでパラメータパネルを確認 ---
from app.domain.entities.cad_model import CADModel, GenerationStatus
from app.domain.value_objects.cad_script import CadScript
import uuid as _uuid

_TEST_SCRIPT = """\
import cadquery as cq
result = (
    cq.Workplane("XY")
    .box(80, 50, 20)
    .faces(">Z").workplane().hole(12)
    .faces(">Z").workplane().center(25, 0).hole(6)
    .faces(">Z").workplane().center(-25, 0).hole(6)
    .edges("|Z").fillet(3)
)
"""

@app.post("/test/generate")
async def test_generate():
    """固定スクリプトで即座にモデル生成（パラメータUI確認用）"""
    model_id = str(_uuid.uuid4())
    cad_model = CADModel(id=model_id, blueprint_id="test", status=GenerationStatus.PENDING)
    cad_model_repo.save(cad_model)

    script = CadScript(content=_TEST_SCRIPT)
    execution_result = cad_executor.execute(script)

    cad_model.stl_path = execution_result.stl_filename
    cad_model.parameters = execution_result.parameters
    cad_model.cad_script = script
    cad_model.status = GenerationStatus.SUCCESS
    cad_model_repo.update(cad_model)

    return {
        "model_id": model_id,
        "status": "success",
        "stl_path": execution_result.stl_filename,
        "parameters": [
            {"name": p.name, "value": p.value, "parameter_type": p.parameter_type.value, "edge_points": p.edge_points}
            for p in execution_result.parameters
        ],
    }
