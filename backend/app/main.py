"""FastAPI エントリポイント。

- リポジトリ・CAD executor・4 視点レンダラは singleton として用意
- VLM 系コンポーネントはリクエストごとに PipelineFactory が組み立てる
"""
from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.infrastructure.cad.cadquery_executor import CadQueryExecutor
from app.infrastructure.persistence.in_memory_blueprint_repository import (
    InMemoryBlueprintRepository,
)
from app.infrastructure.persistence.in_memory_cad_model_repository import (
    InMemoryCADModelRepository,
)
from app.infrastructure.rendering.cadquery_svg_renderer import CadQuerySvgRenderer
from app.infrastructure.rendering.trimesh_pyrender_renderer import (
    TrimeshPyrenderRenderer,
)
from app.presentation.pipeline_factory import PipelineFactory
from app.presentation.routers.blueprint_router import init_router as init_blueprint_router
from app.presentation.routers.blueprint_router import router as blueprint_router
from app.presentation.routers.cad_model_router import init_router as init_cad_model_router
from app.presentation.routers.cad_model_router import router as cad_model_router

CAD_OUTPUT_DIR = "/tmp/cad_output"
os.makedirs(CAD_OUTPUT_DIR, exist_ok=True)

app = FastAPI(title="Blueprint to CAD API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/files", StaticFiles(directory=CAD_OUTPUT_DIR), name="files")

# --- singleton infrastructure ---
blueprint_repo = InMemoryBlueprintRepository()
cad_model_repo = InMemoryCADModelRepository()
cad_executor = CadQueryExecutor(output_dir=CAD_OUTPUT_DIR)
line_renderer = CadQuerySvgRenderer()
shaded_renderer = TrimeshPyrenderRenderer()

pipeline_factory = PipelineFactory(
    output_dir=CAD_OUTPUT_DIR,
    blueprint_repo=blueprint_repo,
    cad_model_repo=cad_model_repo,
    cad_executor=cad_executor,
    line_renderer=line_renderer,
    shaded_renderer=shaded_renderer,
)

init_blueprint_router(blueprint_repo)
init_cad_model_router(blueprint_repo, cad_model_repo, pipeline_factory)

app.include_router(blueprint_router)
app.include_router(cad_model_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
