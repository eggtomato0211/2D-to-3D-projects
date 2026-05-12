# ベストパイプラインのフロー (Claude Opus 4.7 + 両 RAG + Verify-Correct)

DeepCAD N=10 ベンチで **match_score 0.836 / median 0.999 / valid_rate 88.9%** を達成した、本セッション最良の構成のフローを記述する。
結果データ: `backend/experiments/deepcad/compare_opus47_n10_refrag/`

---

## 0. 全体図

```
┌────────────────────────────────────────────────────────────────────┐
│                Phase 1: Generation                                  │
│                                                                     │
│   2D 図面 PNG                                                        │
│        │                                                            │
│   [1] VLM 解析  ─────────  Claude Opus 4.7 (Vision)                  │
│        │                  → DesignStep[] + Clarification[]          │
│        │                                                            │
│   [1.5] Phase 1 cross-check (self-refinement, optional)             │
│        │                                                            │
│        ▼                                                            │
│   [2] スクリプト生成  ──── Claude Opus 4.7                            │
│        │ ┌── CadQuery docs RAG (top-5)                              │
│        │ ├── Reference Code RAG (DeepCAD train top-3)               │
│        │ └── system prompt (4 視点 + セレクタ + 許可リスト)            │
│        │                                                            │
│        ▼ CadScript                                                  │
│   [3] CadQuery 実行 ─────────────────────────────────────┐           │
│        │                                                │           │
│        ├─ コンパイルエラー ─→ fix_script ループ (上限 N)──┘           │
│        │                                                            │
│        ▼ TopoDS_Shape → STL                                         │
└────────────┬───────────────────────────────────────────────────────┘
             │
┌────────────┴───────────────────────────────────────────────────────┐
│                Phase 2: Verify-Correct                              │
│                                                                     │
│   [4] 4 視点レンダリング (Top / Front / Side / Iso, line + shaded)   │
│        │                                                            │
│        ▼                                                            │
│   [5] VLM verifier (Claude Opus 4.7, Vision)                        │
│        │   元 2D 図面 vs candidate 4 視点を比較                       │
│        │   → Discrepancy[] (critical / major / minor)               │
│        │                                                            │
│        ▼                                                            │
│   [6] ループ継続判定                                                  │
│        │  (a) critical > 0                  → corrector へ          │
│        │  (b) critical = 0 ∧ match < th     → 合成 Discrepancy 注入  │
│        │  (c) critical = 0 ∧ match ≥ th     → 終了                  │
│        │                                                            │
│        ▼                                                            │
│   [7] correct_script (Vision-aware)                                 │
│        │   元 2D 図面 + 現状 4 視点 + 残差 + 過去 iter 履歴 を入力     │
│        │   → 修正版 CadScript                                        │
│        │                                                            │
│        └─→ [4] へ戻る (上限 max_iter までループ)                     │
│                                                                     │
│   ベストスナップショット保存:                                          │
│     critical 少 → match_score 高 の順で is_better 判定               │
│     ループ終了時はベスト state を結果に                               │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 1. Phase 1: Generation

### Step 1 — Blueprint 解析 (`AnthropicBlueprintAnalyzer`)

- **モデル**: `claude-opus-4-7` (Vision API)
- **入力**: 2D 図面 PNG
- **出力**:
  - `DesignStep[]` — モデリング手順を自然言語で列挙
  - `Clarification[]` — 不明点に対する確認質問（ユーザー応答可）
  - 構造化された参照ブロック (`**【参照情報・寸法】**` `**【参照情報・特徴】**`) を先頭ステップとして埋め込む
- 「画像から直接パラメータを推定しない、必ず言語化フェーズを通す」が設計原則

### Step 1.5 — Phase 1 cross-check (任意)

- 追加の VLM コールで Step 1 の結果を self-review し、寸法漏れ・特徴抜け・矛盾を洗い出して `DesignStep[]` を補強
- N=10 比較で match_score +0.012、valid_rate +10pt の効果

### Step 2 — スクリプト生成 (`AnthropicScriptGenerator`)

- **モデル**: `claude-opus-4-7`
- `_build_intent_prompt()` でプロンプト組み立て、その中で **両 RAG を retrieve して注入**:

#### 2-1. CadQuery docs RAG (公式ドキュメント検索)

| 項目 | 値 |
|------|----|
| ソース | `backend/app/infrastructure/rag/cadquery_docs/*.md` (workplane, sketch, selectors, apireference 等) |
| chunker | ヘディング階層を保持、1000 char trim |
| embedding | OpenAI `text-embedding-3-small` + L2 正規化 |
| 検索 | cosine similarity, top_k=5, max_chars=2500 |
| クエリ | `op_steps[:6]` の instruction を結合 |
| 挿入位置 | `## CadQuery 公式ドキュメント抜粋（API シグネチャ・使用例の根拠として参照）` |

#### 2-2. Reference Code RAG (DeepCAD train 類似 GT 検索)

| 項目 | 値 |
|------|----|
| ソース | DeepCAD train split から 10,000 件目標 (現状 **992 件構築済み**) |
| エントリ生成 | JSON → TopoDS → STEP → CadQuery 正規化 + JSON walk で擬似コード化 |
| クエリ形式 | **ハイブリッド** — `bbox=[..] diameters=[..] pcd=[..] fillets=[..] chamfers=[..] summary: <natural>` |
| クエリソース | 参照ブロックがあればそれ、無ければ Step 1 と同じ joined_query |
| embedding | OpenAI `text-embedding-3-small` + L2 正規化 |
| 検索 | cosine similarity, top_k=3, max_chars=4000 |
| 挿入位置 | `## 類似 GT 部品の操作列（参照のみ。同じ操作列を真似して CadQuery で書き直すこと）` |
| **リーク防止 3 層** | (1) corpus は train only / (2) `exclude_ids` で評価対象を除外 / (3) hard assert で混入時 fail |

#### 2-3. System prompt の主要要素 (`_build_system_prompt()`)

- Workplane / Sketch / Assembly の使い分け
- Stack 概念 (pending wires/edges)
- セレクタ記法 (`>Z`, `+X`, `|Z`, `%CIRCLE` ...)
- **多段加工で `BRep_API: command not done` を防ぐタグ付きパターン** (`tag("top")` + `workplaneFromTagged`)
- 図面記法 → コード変換早見表 (PCD / obround / ねじ穴の代用 / 全周面取り 等)
- 使用可能メソッドの **許可リスト** と **禁止名 (`tapHole`, `pocket`, `.filter()` 等)**
- Phase 2-δ Corrector 用の "既存 chain を壊さず継ぎ足す" 作法

### Step 3 — スクリプト実行 + fix ループ

- CadQuery で実行 → `TopoDS_Shape` → STL に変換
- コンパイルエラー時は `fix_script()` で自動修正、上限回数まで繰り返し
- エラーメッセージ → ヒント変換 (`_get_error_hints`): `StdFail_NotDone` / `AttributeError` / `pendingWires 空` などに対する具体的な修正方針を prompt に注入

---

## 2. Phase 2: Verify-Correct

### Step 4 — 4 視点レンダリング

- Top / Front / Side / Iso の 4 アングル
- **line drawing** (シルエットや穴の輪郭が明瞭) + **shaded rendering** (体積感) の 2 種類を生成
- いずれも PNG として VLM verifier / corrector に渡す

### Step 5 — VLM verifier (`AnthropicModelVerifier`)

- **モデル**: `claude-opus-4-7` (Vision)
- **入力**: 元 2D 図面 + candidate 4 視点 (line + shaded)
- **出力**: `Discrepancy[]` — 各項目に severity (critical / major / minor) + location_hint + dimension_hint + confidence
- **strengthened P4_SYSTEM プロンプト** (本セッションで強化):
  - `critical` トリガを拡張:
    - silhouette が誤っている
    - ボディ数が違う
    - ≥10% のスケール誤差
    - 軸方向が違う
  - これにより「形状が違うのに critical=0 で通る」誤判定が減少

### Step 6 — ループ継続判定 (`model_comparison.py:run_for_model` / `VerifyAndCorrectUseCase`)

各 iter の終わりに以下のいずれかなら継続:

| 条件 | アクション |
|------|----------|
| `critical_count > 0` | 通常の Discrepancy を Corrector に渡す |
| `critical_count == 0` かつ `match_score < match_threshold` | **合成 Discrepancy を critical として注入** ("全体形状が参照と一致していません。体積一致度 match_score = X.XX, 期待 ≥ Y.YY") |
| `critical_count == 0` かつ `match_score >= match_threshold` | **早期終了** (= 真の合格) |

→ verifier の見落としを `match_score` で補完できる二段判定。

### Step 7 — Correct_script (Vision-aware corrector)

`AnthropicScriptGenerator.correct_script()` で実装。`fix_script` (runtime error 用) とは別プロンプト:

- **入力ペイロード**:
  - `## reference (original 2D drawing)` — 元 2D 図面
  - `## candidate — line drawings (top, front, side, iso)` — 現状 line 4 視点
  - `## candidate — shaded renderings (top, front, side, iso)` — 現状 shaded 4 視点
  - text prompt:
    - 現在の CadScript
    - 検出された不一致 (critical/major/minor で分類)
    - **過去 iter 履歴** (修正対象 → 修正後の残差) — 同じアプローチの繰り返しを防止
    - 修正の方針:
      - 単一不一致モードなら「**この 1 件のみ修正**」
      - 複数なら「critical を全て解消、major は可能な範囲、minor は無理に触らない」
      - **「不一致に直接関係しない箇所は触らない」** (regression 防止)

- 修正された CadScript → Step 4 へ戻ってループ

### ベストスナップショット保存 (`_select_and_apply_best`)

各 iter で以下の優先順位で best 判定:

1. `critical_count` が少ない方が良い
2. 同値なら `match_score` が高い方が良い

ループ終了時、初期生成と各 iter のうち最良の state を結果として返す。
→ Correct が悪化した場合の rollback 効果。

---

## 3. 評価指標 (`_compute_shape_metrics`)

| 指標 | 計算 |
|------|------|
| `compile_rate` | スクリプトが OCP までエラー無く到達した割合 |
| `iou_mean` / `_median` | 24 軸回転 + ICP アライメント後の bbox-正規化 Volume IoU |
| `chamfer_mean` | Chamfer 距離 (正規化後) |
| `chamfer_raw_mean` | Chamfer 距離 (mm 単位) |
| **`match_score`** | **24 軸回転 + ICP 後の絶対スケール Volume IoU** — 1 = 完全一致 |
| `match_score_ge_0_95` | match_score ≥ 0.95 のサンプル比率 |
| `verify_critical_mean` | verifier が critical を 1 件以上検出した割合 |
| `verify_valid_rate` | verifier が critical_count=0 と判定した割合 (= 「意味的に正しい」率) |

ICP アライメントを噛ませることで、座標系が若干ずれていても形状一致度を正確に測れる。本セッションで chamfer が 50–70% 改善したのは ICP 起因。

---

## 4. 主要ファイル

| 役割 | パス |
|------|------|
| Phase 1 Analyzer | `backend/app/infrastructure/vlm/anthropic/anthropic_blueprint_analyzer.py` |
| Script Generator (RAG 注入) | `backend/app/infrastructure/vlm/base/base_script_generator.py` |
| Anthropic Generator (Vision corrector) | `backend/app/infrastructure/vlm/anthropic/anthropic_script_generator.py` |
| OpenAI Generator | `backend/app/infrastructure/vlm/openai/openai_script_generator.py` |
| モデルファクトリ (retriever 配線) | `backend/app/infrastructure/vlm/model_factory.py` |
| CadQuery docs RAG | `backend/app/infrastructure/rag/retriever.py` + `cadquery_docs/` + `cadquery_index/` |
| Reference Code RAG | `backend/app/infrastructure/rag/reference_corpus.py`, `reference_retriever.py`, `reference_codes/`, `reference_index/` |
| Verifier prompts | `backend/app/infrastructure/verification/prompts.py` (P4_SYSTEM 強化版) |
| Verifier (Anthropic) | `backend/app/infrastructure/verification/anthropic_model_verifier.py` |
| Verify-Correct ループ | `backend/app/usecase/verify_and_correct_usecase.py` |
| ベンチランナー | `backend/experiments/deepcad/model_comparison.py` |

---

## 5. ハイパーパラメータと運用値

| パラメータ | 値 | 備考 |
|----------|-----|------|
| 生成モデル | `claude-opus-4-7` | UI default も同上 |
| max_tokens (generation) | 4096 | Anthropic |
| max_tokens (OpenAI) | 16384 | gpt-5 系は `reasoning_effort="low"` |
| docs RAG top_k | 5 | max_chars 2500 |
| Reference RAG top_k | 3 | max_chars 4000 |
| Verify-Correct max_iter | 設定可 | 上限を撤廃すると無限ループ (CLAUDE.md の禁則) |
| match_threshold | (例) 0.95 | ループ早期終了の境界 |
| fix_script ループ上限 | 設定可 | コンパイルエラー時 |

---

## 6. 最終ベンチ値 (再掲)

`compare_opus47_n10_refrag/claude-opus-4-7.summary.json`:

| 指標 | 値 |
|------|-----:|
| `n` | 10 |
| `compile_rate` | 90.0% |
| `chamfer_mean` | 0.0343 |
| `iou_mean` | 0.832 |
| **`match_score_mean`** | **0.836** |
| **`match_score_median`** | **0.999** |
| `match_score_ge_0_95` | 55.6% |
| `match_score_ge_0_80` | 66.7% |
| `verify_critical_mean` | 0.11 |
| `verify_valid_rate` | 88.9% |

ベースライン (RAG なし、loop なし) の 0.725 から **+0.111** の改善、median は 0.999 まで上昇。
