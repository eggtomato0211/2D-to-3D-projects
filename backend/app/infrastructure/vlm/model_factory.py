"""モデル名から analyzer / script_generator を生成するファクトリ。

UI で「使用モデル」を切り替えられるようにするため、リクエストごとに
コンポーネントを差し替えられる形で実装する。

サポートモデルの一覧は SUPPORTED_MODELS で公開され、
GET /models エンドポイントから返される。
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Literal, TypedDict

from app.domain.interfaces.blueprint_analyzer import IBlueprintAnalyzer
from app.domain.interfaces.script_generator import IScriptGenerator

# CadQuery RAG（公式ドキュメント検索）の retriever singleton
_CADQUERY_RETRIEVER = None
_CADQUERY_INDEX_DIR = Path("/app/app/infrastructure/rag/cadquery_index")

# Reference Code RAG（DeepCAD train から取った類似 GT コード）の retriever singleton
_REFERENCE_RETRIEVER = None
_REFERENCE_INDEX_DIR = Path("/app/app/infrastructure/rag/reference_index")


def _get_docs_retriever():
    """初回呼び出し時に index を load。失敗しても None で続行できる。"""
    global _CADQUERY_RETRIEVER
    if _CADQUERY_RETRIEVER is not None:
        return _CADQUERY_RETRIEVER
    if not _CADQUERY_INDEX_DIR.exists():
        return None
    try:
        from app.infrastructure.rag.retriever import CadQueryDocsRetriever
        _CADQUERY_RETRIEVER = CadQueryDocsRetriever(_CADQUERY_INDEX_DIR)
    except Exception:
        _CADQUERY_RETRIEVER = None
    return _CADQUERY_RETRIEVER


def _get_reference_retriever():
    """Reference Code RAG retriever singleton。exclude_ids は呼び出し側で set。"""
    global _REFERENCE_RETRIEVER
    if _REFERENCE_RETRIEVER is not None:
        return _REFERENCE_RETRIEVER
    if not _REFERENCE_INDEX_DIR.exists():
        return None
    try:
        from app.infrastructure.rag.reference_retriever import ReferenceCodeRetriever
        _REFERENCE_RETRIEVER = ReferenceCodeRetriever(_REFERENCE_INDEX_DIR)
    except Exception:
        _REFERENCE_RETRIEVER = None
    return _REFERENCE_RETRIEVER


Provider = Literal["anthropic", "openai"]


class ModelSpec(TypedDict):
    id: str            # API model identifier
    label: str         # UI 表示名
    provider: Provider
    description: str   # 説明
    default: bool      # 初期選択かどうか


# UI から選択可能なモデル一覧
# 並び順 = UI での表示順
SUPPORTED_MODELS: list[ModelSpec] = [
    {
        "id": "claude-opus-4-7",
        "label": "Claude Opus 4.7",
        "provider": "anthropic",
        "description": "Anthropic 最新フラッグシップ。compile 100%、意味的正確性 (valid rate) 優位。",
        "default": True,  # 既定
    },
    {
        "id": "claude-opus-4-6",
        "label": "Claude Opus 4.6",
        "provider": "anthropic",
        "description": "Opus 系の安定版（旧トークナイザ）。コスパ良。形状一致 (match_score) で N=10 トップ。",
        "default": False,
    },
    {
        "id": "claude-sonnet-4-6",
        "label": "Claude Sonnet 4.6",
        "provider": "anthropic",
        "description": "中位モデル。コスト 1/5 で実用域。",
        "default": False,
    },
    {
        "id": "claude-haiku-4-5",
        "label": "Claude Haiku 4.5",
        "provider": "anthropic",
        "description": "軽量モデル。スクリーニング用。",
        "default": False,
    },
    {
        "id": "gpt-5.5",
        "label": "GPT-5.5",
        "provider": "openai",
        "description": "OpenAI 最新フラッグシップ。compile 90%+ で形状品質も高い。",
        "default": False,
    },
    {
        "id": "gpt-5",
        "label": "GPT-5",
        "provider": "openai",
        "description": "コスパ最強。形状品質トップクラス。",
        "default": False,
    },
    {
        "id": "gpt-5-mini",
        "label": "GPT-5 mini",
        "provider": "openai",
        "description": "超軽量。デモ・大量実行用。",
        "default": False,
    },
    {
        "id": "gpt-4.1",
        "label": "GPT-4.1",
        "provider": "openai",
        "description": "GPT-4 系の改良版。",
        "default": False,
    },
    {
        "id": "gpt-4o",
        "label": "GPT-4o",
        "provider": "openai",
        "description": "GPT-4 系の旧フラッグシップ。",
        "default": False,
    },
]


# 既定モデル（main.py 起動時の初期値、UI からの選択がない場合のフォールバック）
DEFAULT_MODEL: str = next(
    (m["id"] for m in SUPPORTED_MODELS if m["default"]),
    SUPPORTED_MODELS[0]["id"],
)


def _provider_of(model_id: str) -> Provider:
    for m in SUPPORTED_MODELS:
        if m["id"] == model_id:
            return m["provider"]
    raise ValueError(f"unknown model: {model_id}")


def is_supported(model_id: str) -> bool:
    return any(m["id"] == model_id for m in SUPPORTED_MODELS)


def build_analyzer(model_id: str = DEFAULT_MODEL) -> IBlueprintAnalyzer:
    """`model_id` に応じた analyzer を構築する。"""
    provider = _provider_of(model_id)
    if provider == "anthropic":
        from app.infrastructure.vlm.anthropic.anthropic_blueprint_analyzer import (
            AnthropicBlueprintAnalyzer,
        )
        return AnthropicBlueprintAnalyzer(
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            model=model_id,
        )
    if provider == "openai":
        from app.infrastructure.vlm.openai.openai_blueprint_analyzer import (
            OpenAIBlueprintAnalyzer,
        )
        return OpenAIBlueprintAnalyzer(
            api_key=os.getenv("OPENAI_API_KEY"),
            model=model_id,
        )
    raise ValueError(f"unsupported provider: {provider}")


def build_verifier(model_id: str = DEFAULT_MODEL):
    """`model_id` に応じた model_verifier を構築する。

    Anthropic 系は AnthropicModelVerifier、OpenAI 系は OpenAIModelVerifier。
    """
    provider = _provider_of(model_id)
    if provider == "anthropic":
        from app.infrastructure.verification.anthropic_model_verifier import (
            AnthropicModelVerifier,
        )
        return AnthropicModelVerifier(
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            model=model_id,
        )
    if provider == "openai":
        from app.infrastructure.verification.openai_model_verifier import (
            OpenAIModelVerifier,
        )
        return OpenAIModelVerifier(
            api_key=os.getenv("OPENAI_API_KEY"),
            model=model_id,
        )
    raise ValueError(f"unsupported provider: {provider}")


def build_script_generator(model_id: str = DEFAULT_MODEL,
                           exclude_ids: set[str] | None = None) -> IScriptGenerator:
    """`model_id` に応じた script_generator を構築する。

    - CadQuery RAG（docs_retriever）を自動注入
    - Reference Code RAG（ref_retriever）も自動注入。exclude_ids を指定すれば
      評価対象 ID を retrieve から除外（データリーク防止）
    """
    provider = _provider_of(model_id)
    docs_retriever = _get_docs_retriever()
    ref_retriever = _get_reference_retriever()
    if ref_retriever is not None and exclude_ids:
        ref_retriever.set_exclude_ids(exclude_ids)
    if provider == "anthropic":
        from app.infrastructure.vlm.anthropic.anthropic_script_generator import (
            AnthropicScriptGenerator,
        )
        return AnthropicScriptGenerator(
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            model=model_id,
            docs_retriever=docs_retriever,
            ref_retriever=ref_retriever,
        )
    if provider == "openai":
        from app.infrastructure.vlm.openai.openai_script_generator import (
            OpenAIScriptGenerator,
        )
        return OpenAIScriptGenerator(
            api_key=os.getenv("OPENAI_API_KEY"),
            model=model_id,
            docs_retriever=docs_retriever,
            ref_retriever=ref_retriever,
        )
    raise ValueError(f"unsupported provider: {provider}")
