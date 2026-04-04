from fastapi import FastAPI
import os

# Infrastructure
from app.infrastructure.persistence.in_memory_blueprint_repository import InMemoryBlueprintRepository
from app.infrastructure.persistence.in_memory_cad_model_repository import InMemoryCADModelRepository
from app.infrastructure.vlm.openai.openai_blueprint_analyzer import OpenAIBlueprintAnalyzer
from app.infrastructure.vlm.gemini.gemini_script_generator import GeminiScriptGenerator
from app.infrastructure.cad.cadquery_executor import CadQueryExecutor

# UseCase
from app.usecase.analyze_blueprint_usecase import AnalyzeBlueprintUseCase
from app.usecase.generate_script_usecase import GenerateScriptUseCase
from app.usecase.execute_script_usecase import ExecuteScriptUseCase
from app.usecase.generate_cad_usecase import GenerateCadUseCase

# Presentation
from app.presentation.routers.blueprint_router import router as blueprint_router
from app.presentation.routers.blueprint_router import init_router as init_blueprint_router
from app.presentation.routers.cad_model_router import router as cad_model_router
from app.presentation.routers.cad_model_router import init_router as init_cad_model_router

app = FastAPI(title="Blueprint to CAD API")

# --- DI 組み立て ---

# リポジトリ
blueprint_repo = InMemoryBlueprintRepository()
cad_model_repo = InMemoryCADModelRepository()

# Infrastructure（外部サービス）
blueprint_analyzer = OpenAIBlueprintAnalyzer(
    api_key=os.getenv("OPENAI_API_KEY"),
)
script_generator = GeminiScriptGenerator(
    api_key=os.getenv("GEMINI_API_KEY"),
)
cad_executor = CadQueryExecutor(output_dir="/tmp/cad_output")

# UseCase
analyze_uc = AnalyzeBlueprintUseCase(blueprint_repo, cad_model_repo, blueprint_analyzer)
generate_script_uc = GenerateScriptUseCase(cad_model_repo, script_generator)
execute_script_uc = ExecuteScriptUseCase(cad_model_repo, cad_executor)
generate_cad_uc = GenerateCadUseCase(analyze_uc, generate_script_uc, execute_script_uc)

# ルーターに依存性を注入
init_blueprint_router(blueprint_repo)
init_cad_model_router(blueprint_repo, cad_model_repo, generate_cad_uc)

# ルーター登録
app.include_router(blueprint_router)
app.include_router(cad_model_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
