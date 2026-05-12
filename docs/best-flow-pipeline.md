# ベストフロー実装ガイド

UI 側に組み込んだ、本セッション最良の構成 (Claude Opus 4.7 + CadQuery docs RAG + Reference Code RAG + Verify-Correct ループ) を、本リポジトリのクリーンアーキテクチャ上でどう実装したかを記述する。

ベンチ結果は `docs/experiments-summary.md` と `docs/best-pipeline-flow.md` を参照。

---

## 1. レイヤ構成

```
Presentation  →  Usecase  →  Domain  ←  Infrastructure
   (router)     (orchestrate)   (pure)      (LLM, CAD, RAG, render)
```

- **Domain**: 純粋 Python のみ。VO・Entity・IF を置く（外部依存禁止）。
- **Usecase**: Domain の IF に依存しながら手順を組む。infrastructure を直接 import しない。
- **Infrastructure**: VLM (Anthropic / OpenAI), CadQuery, RAG, 4 視点レンダリング等の具体実装。
- **Presentation**: FastAPI ルータと DTO。`PipelineFactory` が VLM 切り替えに合わせて Usecase をその都度組み立てる。

---

## 2. 主要パイプライン

```
2D 図面 PNG/PDF
   │
   ▼
[Step 1] BlueprintAnalyzer (Opus 4.7 Vision)
   - 構造化抽出 (dimensions_table / feature_inventory)
   - cross-check (self-refinement)
   → DesignStep[] + Clarification[]
   │
   ▼
[Step 2] ScriptGenerator (Opus 4.7)
   - CadQuery docs RAG (top-5) を注入
   - Reference Code RAG (top-3) を注入
   → CadScript
   │
   ▼
[Step 3] CadQueryExecutor
   - STL + STEP を書き出し
   → ExecutionResult
   │
   ▼
[Step 4] 4 視点レンダリング
   - CadQuerySvgRenderer: STEP → line drawing 4 views
   - TrimeshPyrenderRenderer: STL → shaded 4 views
   │
   ▼
[Step 5] ModelVerifier (Opus 4.7 Vision)
   - 元 2D 図面 vs 候補 4 視点を比較
   → VerificationResult (Discrepancy[])
   │
   ▼
[Step 6] Verify-Correct ループ
   - critical > 0 の場合 corrector で修正
   - corrector も Vision で画像入力 + 過去 iter 履歴を考慮
   - best 状態を track (critical → major → minor 順)
   - degradation 検出で早期終了 / max_iter 到達で終了
   → CADModel (best snapshot)
```

---

## 3. ファイル対応表

### Domain (`backend/app/domain/`)

| ファイル | 内容 |
|---|---|
| `entities/cad_model.py` | パイプライン状態を保持。`verification_result` / `iteration_history` / `step_path` / `model_provider_id` を追加 |
| `value_objects/discrepancy.py` | 1 件の不一致 (severity + 期待/現状 + ヒント) |
| `value_objects/verification.py` | `VerificationResult` (`is_valid` + Discrepancy リスト + 件数集計) |
| `value_objects/four_view_image.py` | 4 視点 PNG バイト列 |
| `value_objects/iteration_attempt.py` | corrector の試行履歴 |
| `value_objects/loop_config.py` | ループ上限・degradation 停止 |
| `value_objects/verify_outcome.py` | 1 回分の verify 結果 + 視覚情報 (再レンダ防止) |
| `interfaces/line_drawing_four_view_renderer.py` | STEP → 線画 4 視点 |
| `interfaces/shaded_four_view_renderer.py` | STL → 影付き 4 視点 |
| `interfaces/cadquery_docs_retriever.py` | 公式 docs RAG |
| `interfaces/reference_code_retriever.py` | DeepCAD 等の参照 GT RAG (set_exclude_ids 付き) |
| `interfaces/model_verifier.py` | `verify(blueprint, line_views, shaded_views) -> VerificationResult` |
| `interfaces/script_generator.py` | `correct_script` を IF に追加 (Vision 引数オプション) |

### Infrastructure (`backend/app/infrastructure/`)

| ファイル | 内容 |
|---|---|
| `rendering/views.py` | カメラ規約 (top/front/side/iso) |
| `rendering/cadquery_svg_renderer.py` | CadQuery SVG → cairosvg PNG |
| `rendering/trimesh_pyrender_renderer.py` | OSMesa headless で影付きレンダ |
| `rag/chunker.py` | Markdown ヘッダー単位の chunk 分割 |
| `rag/embedder.py` | OpenAI `text-embedding-3-small` の薄ラッパー |
| `rag/index.py` | npz + json で index を保存/ロード |
| `rag/cadquery_docs_retriever.py` | 公式 docs 抜粋の cosine 類似検索 |
| `rag/reference_corpus.py` | DeepCAD JSON → CadQuery 風擬似コード walker |
| `rag/reference_code_retriever.py` | 類似 GT 検索 + 3 層リーク防止 |
| `rag/scripts/build_index.py` | docs から index を構築 |
| `rag/scripts/build_reference_corpus.py` | DeepCAD から corpus を構築 |
| `rag/scripts/build_reference_index.py` | corpus を embedding して index 化 |
| `verification/prompts.py` | 強化版 P4 system / user prompt |
| `verification/_parsing.py` | 共有 JSON パーサ |
| `verification/anthropic_model_verifier.py` | Claude (Vision) Verifier |
| `verification/openai_model_verifier.py` | GPT (Vision) Verifier |
| `vlm/base/system_prompt.py` | CadQuery 公式 + JIS/ISO + 図面記法早見表 |
| `vlm/base/_error_hints.py` | エラー文字列 → 修正ヒント |
| `vlm/base/_prompts.py` | generate / fix / correct / modify_parameters |
| `vlm/base/_analyzer_prompt.py` | Analyzer system prompt + 構造化抽出ブロック |
| `vlm/base/_response_parser.py` | JSON → DesignStep/Clarification + 参照ブロック整形 |
| `vlm/base/_image_io.py` | PDF→PNG / 4MB 圧縮 |
| `vlm/base/dimension_cross_check.py` | Phase 1 self-refinement |
| `vlm/base/base_blueprint_analyzer.py` | analyze 全体の orchestration |
| `vlm/base/base_script_generator.py` | prompt 組立 + 両 RAG 注入 |
| `vlm/anthropic/_image_blocks.py` | Anthropic image content block |
| `vlm/anthropic/anthropic_blueprint_analyzer.py` | Vision analyze + cross-check |
| `vlm/anthropic/anthropic_script_generator.py` | Vision-aware correct_script |
| `vlm/openai/_retry.py` | 指数バックオフリトライ |
| `vlm/openai/openai_blueprint_analyzer.py` | GPT-5/4o 用 analyze + cross-check |
| `vlm/openai/openai_script_generator.py` | reasoning_effort=low 対応 |
| `vlm/model_factory.py` | SUPPORTED_MODELS + retriever singleton + build_* |
| `cad/cadquery_executor.py` | STL + STEP を書き出し |

### Usecase (`backend/app/usecase/`)

| ファイル | 内容 |
|---|---|
| `verify_cad_model_usecase.py` | 1 回分の verify (4 視点レンダ → verifier) |
| `verify_and_correct_usecase.py` | 検証→修正ループ。best snapshot で rollback |
| `execute_script_usecase.py` | STEP path も CADModel に保存するよう更新 |
| `update_parameters_usecase.py` | STEP path も保存 |
| `analyze_blueprint_usecase.py` / `generate_*` | 既存のまま |

### Presentation (`backend/app/presentation/`)

| ファイル | 内容 |
|---|---|
| `pipeline_factory.py` | リクエストごとに usecase をビルド (VLM model 差し替え対応) |
| `schemas/cad_model_schema.py` | VerificationResultDTO / DiscrepancyDTO / VlmModelInfo を追加 |
| `routers/cad_model_router.py` | `/vlm-models`, `/blueprints/{id}/generate` (model 受領), `/models/{id}/verify-and-correct` |

### Frontend (`frontend/src/`)

| ファイル | 内容 |
|---|---|
| `entities/cad-model/model/types.ts` | `Discrepancy` / `VerificationResult` 型を追加 |
| `features/select-model/api/vlmModels.ts` | `GET /vlm-models` |
| `features/select-model/ui/ModelSelector.tsx` | ドロップダウン (default 自動選択) |
| `features/verify-and-correct/api/verifyAndCorrect.ts` | `POST /models/{id}/verify-and-correct` |
| `features/verify-and-correct/ui/VerifyAndCorrectPanel.tsx` | ボタン + 不一致表示 |
| `widgets/blueprint-editor/ui/BlueprintEditor.tsx` | ModelSelector + VerifyAndCorrectPanel を統合 |

---

## 4. 初期セットアップ

```bash
# 1. コンテナ起動
docker-compose up --build

# 2. CadQuery docs index を構築 (両 RAG のうち軽い方)
docker compose exec backend python -m app.infrastructure.rag.scripts.build_index

# 3. (任意) DeepCAD reference corpus + index を構築
#    DeepCAD のデータが /app/data/deepcad に必要。corpus 構築は数時間。
docker compose exec backend python -m app.infrastructure.rag.scripts.build_reference_corpus
docker compose exec backend python -m app.infrastructure.rag.scripts.build_reference_index
```

index が無い場合は retriever が `None` となり、両 RAG なしの素の VLM で動作する（フォールバック）。

---

## 5. 環境変数

| 変数 | デフォルト | 役割 |
|---|---|---|
| `ANTHROPIC_API_KEY` | 必須 | Claude 用 |
| `OPENAI_API_KEY` | 必須 | GPT + embedding 用 |
| `PHASE1_STRUCTURED` | `1` | 構造化抽出 (dimensions_table / feature_inventory) を有効化 |
| `PHASE1_CROSS_CHECK` | `1` | Phase 1 self-refinement 追加 LLM 呼び出し。コスト削減で 0 にしてもよい |

---

## 6. API 一覧

| メソッド | パス | 用途 |
|---|---|---|
| GET | `/vlm-models` | サポート対象 VLM とデフォルト ID |
| POST | `/blueprints/{bp_id}/generate` | 生成 (body: `{ "model": "claude-opus-4-7" }`) |
| POST | `/blueprints/{bp_id}/confirm-clarifications?model_id={cad_id}` | 確認回答後の再開 |
| POST | `/models/{cad_id}/verify-and-correct` | 検証 + 自動修正ループ |
| GET | `/models/{cad_id}` | CADModel の現状取得 |
| PUT | `/models/{cad_id}/parameters` | パラメータ変更 |

レスポンスの `verification` フィールドに `is_valid` / `critical_count` / `discrepancies[]` が入る。

---

## 7. デフォルト VLM

`backend/app/infrastructure/vlm/model_factory.py` の `SUPPORTED_MODELS` で `default=True` のもの。本実装では `claude-opus-4-7`。UI は起動時に `/vlm-models` を叩いてこの default を反映する。

---

## 8. 拡張ポイント

- **新しい VLM モデル**: `SUPPORTED_MODELS` に追加し、provider が `anthropic` / `openai` ならそのまま動く。別 provider なら `model_factory.build_*` を分岐させる。
- **別の RAG ソース**: `ICadQueryDocsRetriever` / `IReferenceCodeRetriever` を実装し、`model_factory.get_*_retriever()` を差し替える。
- **新しいレンダラ**: `ILineDrawingFourViewRenderer` / `IShadedFourViewRenderer` を実装し、`main.py` で差し替える。
- **ループ設定**: `LoopConfig` を `PipelineFactory.build_verify_and_correct` に渡せば挙動を変えられる。
