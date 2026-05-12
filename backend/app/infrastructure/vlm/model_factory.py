"""モデル ID から各種コンポーネント (analyzer / script_generator / verifier) を生成するファクトリ。

UI から「使用モデル」を選べるようにするため、リクエストごとにコンポーネントを
差し替え可能な形で組み立てる。RAG retriever は singleton で共有。

サポートモデル一覧は `SUPPORTED_MODELS` で公開され、GET /models から返される。
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Literal, Optional, TypedDict

from app.domain.interfaces.blueprint_analyzer import IBlueprintAnalyzer
from app.domain.interfaces.cadquery_docs_retriever import ICadQueryDocsRetriever
from app.domain.interfaces.model_verifier import IModelVerifier
from app.domain.interfaces.reference_code_retriever import IReferenceCodeRetriever
from app.domain.interfaces.script_generator import IScriptGenerator

Provider = Literal["anthropic", "openai"]


class ModelSpec(TypedDict):
    id: str
    label: str
    provider: Provider
    description: str
    default: bool


SUPPORTED_MODELS: list[ModelSpec] = [
    {
        "id": "claude-opus-4-7",
        "label": "Claude Opus 4.7",
        "provider": "anthropic",
        "description": "Anthropic 最新フラッグシップ。両 RAG 込みで match_score 0.836 を達成。",
        "default": True,
    },
    {
        "id": "claude-opus-4-6",
        "label": "Claude Opus 4.6",
        "provider": "anthropic",
        "description": "Opus 系の安定版。コスパ良。",
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
        "id": "gpt-5",
        "label": "GPT-5",
        "provider": "openai",
        "description": "OpenAI 系。CadQuery docs RAG 単体で形状品質トップクラス。",
        "default": False,
    },
    {
        "id": "gpt-5-mini",
        "label": "GPT-5 mini",
        "provider": "openai",
        "description": "超軽量。デモ用。",
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


DEFAULT_MODEL: str = next(
    (m["id"] for m in SUPPORTED_MODELS if m["default"]),
    SUPPORTED_MODELS[0]["id"],
)


def is_supported(model_id: str) -> bool:
    return any(m["id"] == model_id for m in SUPPORTED_MODELS)


def _provider_of(model_id: str) -> Provider:
    for m in SUPPORTED_MODELS:
        if m["id"] == model_id:
            return m["provider"]
    raise ValueError(f"unknown model: {model_id}")


# --- RAG retriever singletons ---
_CADQUERY_INDEX_DIR = Path("/app/app/infrastructure/rag/cadquery_index")
_REFERENCE_INDEX_DIR = Path("/app/app/infrastructure/rag/reference_index")

_docs_retriever: Optional[ICadQueryDocsRetriever] = None
_ref_retriever: Optional[IReferenceCodeRetriever] = None


def get_docs_retriever() -> Optional[ICadQueryDocsRetriever]:
    """CadQuery docs RAG の retriever（初回呼び出しで lazy ロード）。"""
    global _docs_retriever
    if _docs_retriever is not None:
        return _docs_retriever
    if not _CADQUERY_INDEX_DIR.exists():
        return None
    try:
        from app.infrastructure.rag.cadquery_docs_retriever import CadQueryDocsRetriever
        _docs_retriever = CadQueryDocsRetriever(_CADQUERY_INDEX_DIR)
    except Exception:
        _docs_retriever = None
    return _docs_retriever


def get_reference_retriever() -> Optional[IReferenceCodeRetriever]:
    """Reference Code RAG の retriever（初回呼び出しで lazy ロード）。"""
    global _ref_retriever
    if _ref_retriever is not None:
        return _ref_retriever
    if not _REFERENCE_INDEX_DIR.exists():
        return None
    try:
        from app.infrastructure.rag.reference_code_retriever import ReferenceCodeRetriever
        _ref_retriever = ReferenceCodeRetriever(_REFERENCE_INDEX_DIR)
    except Exception:
        _ref_retriever = None
    return _ref_retriever


# --- builders ---
def build_analyzer(model_id: str = DEFAULT_MODEL) -> IBlueprintAnalyzer:
    provider = _provider_of(model_id)
    if provider == "anthropic":
        from app.infrastructure.vlm.anthropic.anthropic_blueprint_analyzer import (
            AnthropicBlueprintAnalyzer,
        )
        return AnthropicBlueprintAnalyzer(
            api_key=os.environ["ANTHROPIC_API_KEY"],
            model=model_id,
        )
    from app.infrastructure.vlm.openai.openai_blueprint_analyzer import (
        OpenAIBlueprintAnalyzer,
    )
    return OpenAIBlueprintAnalyzer(
        api_key=os.environ["OPENAI_API_KEY"],
        model=model_id,
    )


def build_script_generator(
    model_id: str = DEFAULT_MODEL,
    exclude_ids: Optional[set[str]] = None,
) -> IScriptGenerator:
    """`model_id` の script_generator を組み立てて返す。

    両 RAG を自動注入。`exclude_ids` を指定すれば Reference Code RAG の
    retrieve から該当 ID を除外（評価時のデータリーク防止）。
    """
    provider = _provider_of(model_id)
    docs = get_docs_retriever()
    ref = get_reference_retriever()
    if ref is not None and exclude_ids:
        ref.set_exclude_ids(exclude_ids)

    if provider == "anthropic":
        from app.infrastructure.vlm.anthropic.anthropic_script_generator import (
            AnthropicScriptGenerator,
        )
        return AnthropicScriptGenerator(
            api_key=os.environ["ANTHROPIC_API_KEY"],
            model=model_id,
            docs_retriever=docs,
            ref_retriever=ref,
        )
    from app.infrastructure.vlm.openai.openai_script_generator import (
        OpenAIScriptGenerator,
    )
    return OpenAIScriptGenerator(
        api_key=os.environ["OPENAI_API_KEY"],
        model=model_id,
        docs_retriever=docs,
        ref_retriever=ref,
    )


def build_verifier(model_id: str = DEFAULT_MODEL) -> IModelVerifier:
    provider = _provider_of(model_id)
    if provider == "anthropic":
        from app.infrastructure.verification.anthropic_model_verifier import (
            AnthropicModelVerifier,
        )
        return AnthropicModelVerifier(
            api_key=os.environ["ANTHROPIC_API_KEY"],
            model=model_id,
        )
    from app.infrastructure.verification.openai_model_verifier import (
        OpenAIModelVerifier,
    )
    return OpenAIModelVerifier(
        api_key=os.environ["OPENAI_API_KEY"],
        model=model_id,
    )
