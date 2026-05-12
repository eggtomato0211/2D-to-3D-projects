"""IBlueprintAnalyzer の共通ベースクラス。

- 画像の前処理（PDF→PNG、4MB 圧縮、base64 化）
- system prompt の組立
- VLM 応答 JSON のパース
- 構造化抽出が有効ならば Phase 1 self-refinement（cross-check）を回す
"""
from __future__ import annotations

import json
import os
from abc import abstractmethod

from loguru import logger

from app.domain.entities.blueprint import Blueprint
from app.domain.interfaces.blueprint_analyzer import IBlueprintAnalyzer
from app.domain.value_objects.clarification import Clarification
from app.domain.value_objects.design_step import DesignStep

from . import _response_parser
from ._analyzer_prompt import build_system_prompt, structured_extraction_enabled
from ._image_io import encode_image_for_vlm
from .dimension_cross_check import (
    CROSS_CHECK_SYSTEM_PROMPT,
    apply_corrections,
    build_cross_check_user_text,
    extract_json as _cc_extract_json,
)


def cross_check_enabled() -> bool:
    """Phase 1 self-refinement（追加 LLM 呼び出し）を有効にするか。

    既定: 有効。コスト削減で OFF にしたい場合は `PHASE1_CROSS_CHECK=0` を設定。
    """
    return os.environ.get("PHASE1_CROSS_CHECK", "1") not in ("0", "false", "False", "")


class BaseBlueprintAnalyzer(IBlueprintAnalyzer):

    def analyze(
        self, blueprint: Blueprint
    ) -> tuple[list[DesignStep], list[Clarification]]:
        image_data, mime = encode_image_for_vlm(
            blueprint.file_path, blueprint.content_type
        )
        content = self._call_api(image_data, mime)
        if cross_check_enabled() and structured_extraction_enabled():
            try:
                refined = self._run_cross_check(content, image_data, mime)
                if refined is not None:
                    content = refined
            except Exception as e:
                logger.warning(
                    f"[cross-check] failed, using original: {type(e).__name__}: {e}"
                )
        return _response_parser.parse_analyzer_response(content)

    # ---- internal helpers ----
    def _build_system_prompt(self) -> str:
        return build_system_prompt()

    def _run_cross_check(
        self, original_content: str, image_data: str, mime: str
    ) -> str | None:
        """初回 analyze 結果に対する VLM 自己整合性チェック。

        訂正があれば訂正済み JSON 文字列を返す。訂正なし / 失敗時は None。
        """
        try:
            data = json.loads(_response_parser.extract_json(original_content))
        except Exception:
            return None
        dims = data.get("dimensions_table") or []
        features = data.get("feature_inventory") or []
        if not dims and not features:
            return None

        user_text = build_cross_check_user_text(dims, features)
        raw = self._call_cross_check(
            image_data, mime,
            system_prompt=CROSS_CHECK_SYSTEM_PROMPT,
            user_text=user_text,
        )
        if not raw:
            return None
        cc = _cc_extract_json(raw)
        if not cc.get("needs_correction"):
            return None

        new_dims, new_feats = apply_corrections(
            dims, features, cc.get("corrections", {})
        )
        data["dimensions_table"] = new_dims
        data["feature_inventory"] = new_feats
        logger.info(
            f"[cross-check] applied: dims {len(dims)}->{len(new_dims)}, "
            f"features {len(features)}->{len(new_feats)}; summary={cc.get('summary')}"
        )
        return json.dumps(data, ensure_ascii=False)

    # ---- subclass extension points ----
    @abstractmethod
    def _call_api(self, image_data: str, mime: str) -> str:
        """初回解析のための VLM 呼び出し。JSON テキストを返す。"""
        ...

    def _call_cross_check(
        self, image_data: str, mime: str,
        system_prompt: str, user_text: str,
    ) -> str:
        """cross-check 用の追加 VLM 呼び出し。

        既定実装は空文字 (= cross-check 無効化)。Anthropic/OpenAI は override する。
        """
        return ""
