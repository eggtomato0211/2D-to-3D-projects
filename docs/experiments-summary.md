# Blueprint-to-CAD 実験結果サマリ

このドキュメントは、DeepCAD データセット上で実施したモデル比較・精度向上施策の実験結果をまとめたものです。
各実験のスクリプトは `backend/experiments/deepcad/` 配下、結果 JSON は同じディレクトリの `compare_*/` または `match_score_*/` に保存されています。

---

## 1. 評価指標

| 指標 | 定義 | 範囲 |
|------|------|------|
| `compile_rate` | 生成スクリプトがエラーなく実行できた割合 | 0–100% |
| `iou_mean` / `iou_median` | 24軸回転 + ICP アライメント後の Volume IoU | 0–1 |
| `chamfer_mean` | Chamfer 距離（bbox 正規化後） | 0 が完全一致 |
| `chamfer_raw_mean` | Chamfer 距離（正規化前、絶対スケール） | mm 単位 |
| **`match_score_mean`** | 24軸回転 + ICP 後の絶対スケール Volume IoU。1 = 完全一致 | 0–1 |
| `match_score_median` | 同上の中央値 | 0–1 |
| `match_score_ge_0_95` | match_score ≥ 0.95 のサンプル比率（「ほぼ同一」率） | 0–1 |
| `match_score_ge_0_80` | match_score ≥ 0.80 のサンプル比率 | 0–1 |
| `verify_critical_mean` | VLM verifier が critical 不一致を 1 件以上検出した割合 | 0–1 |
| `verify_valid_rate` | VLM verifier が `critical_count = 0` と判定した割合（=「意味的に正しい」率） | 0–100% |

> `match_score` は本セッションで導入した主要指標。compile が通っても見た目が違う形状を弾けるよう、絶対スケールの Volume IoU を 24 軸の回転と ICP で最適アライメントしてから測定。

---

## 2. 実験タイムライン

| # | 実験 | ディレクトリ | 主目的 |
|---|------|------------|--------|
| 1 | 6 モデル N=10 比較 (ベースライン) | `match_score_n10_6models/` | 各モデルの素の性能を測る |
| 2 | opus-4-7 N=10 ベースライン | `compare_opus47_n10_rag/` | (※ ディレクトリ名は便宜、内容は基礎構成) |
| 3 | opus-4-7 + Verify-Correct loop | `compare_opus47_n10_loop/` | Phase 2 ループの効果 |
| 4 | opus-4-7 + verifier v2 prompts | `compare_opus47_n10_loop_v2/` | verifier 厳格化 + match ベース継続 |
| 5 | opus-4-7 + Phase 1 cross-check | `compare_opus47_n10_rag_cc/` | self-refinement の効果 |
| 6 | opus-4-7 + **CadQuery docs RAG + Reference Code RAG** | `compare_opus47_n10_refrag/` | RAG 二段の効果 (本セッションの最終構成) |
| 7 | gpt-5 + CadQuery docs RAG | `compare_gpt5_n10_rag/` | OpenAI 系での RAG 効果検証 |
| 8 | gpt-5 N=200 ベースライン | `compare_gpt5_n200/` | 統計的に信頼できる素性能 |

---

## 3. ベースライン: 6 モデル N=10 比較

`match_score_n10_6models/comparison.json`

| モデル | compile | match_score_mean | match_score_median | ≥0.95 | ≥0.80 | valid_rate | critical_mean |
|--------|--------:|-----------------:|-------------------:|------:|------:|-----------:|--------------:|
| **claude-opus-4-6** | 90% | **0.793** | **1.000** | 55.6% | 66.7% | 66.7% | 0.44 |
| claude-sonnet-4-6   | 90% | 0.765 | 1.000 | 55.6% | 55.6% | **88.9%** | 0.11 |
| claude-haiku-4-5    | 30% | 0.573 | 0.495 | 33.3% | 33.3% | 33.3% | 1.00 |
| gpt-5.5             | 90% | 0.701 | 0.962 | 55.6% | 66.7% | 71.4% | 0.29 |
| gpt-5               | 80% | 0.683 | 0.809 | 50.0% | 50.0% | 62.5% | 0.50 |
| gpt-5-mini          | 80% | 0.528 | 0.471 | 25.0% | 37.5% | 42.9% | 0.71 |

**所見:**
- 形状一致のトップは `claude-opus-4-6` (0.793)。
- 意味的妥当性 (`valid_rate`) のトップは `claude-sonnet-4-6` (88.9%)。コスト 1/5 で valid 率が opus-4-6 を上回る。
- `claude-haiku-4-5` は compile_rate 30% で実用域に届かない。
- `gpt-5-mini` は match_score も低く、デモ・大量実行用以外には推奨しない。

---

## 4. opus-4-7 系の改善積み上げ (N=10、同一サンプル ID)

opus-4-7 を基準に、施策を 1 つずつ積み上げた結果。すべて `match_score_n10_6models/selected_ids.json` と同じ 10 サンプル ID で評価。

| 構成 | ディレクトリ | compile | match_mean | match_median | ≥0.95 | ≥0.80 | valid_rate | critical_mean |
|------|------------|--------:|-----------:|-------------:|------:|------:|-----------:|--------------:|
| ベースライン | `compare_opus47_n10_rag/` | 100% | 0.725 | 0.892 | 50.0% | 50.0% | 90.0% | 0.10 |
| + Verify-Correct loop | `compare_opus47_n10_loop/` | 100% | 0.720 | 0.892 | 50.0% | 50.0% | 90.0% | 0.20 |
| + verifier v2 prompts | `compare_opus47_n10_loop_v2/` | 100% | 0.730 | 0.912 | 50.0% | 60.0% | 70.0% | 0.30 |
| + Phase 1 cross-check | `compare_opus47_n10_rag_cc/` | 100% | 0.737 | 0.950 | 50.0% | 60.0% | 80.0% | 0.40 |
| **+ CadQuery docs RAG**<br>**+ Reference Code RAG** | `compare_opus47_n10_refrag/` | 90% | **0.836** | **0.999** | **55.6%** | **66.7%** | 88.9% | 0.11 |

**所見:**
- Verify-Correct loop 単体ではほぼ無変化 (0.725 → 0.720)。verifier が「軽すぎる」状態では効果が出ない。
- verifier prompt 強化 (`critical` トリガを silhouette/body count/scale/axis に拡張) で +0.010、cross-check で +0.012。微増だが累積で効く。
- **最大のジャンプは Reference Code RAG 追加時の +0.099** (0.737 → 0.836)。本セッション全体での累積効果は **+0.111** (0.725 → 0.836)。
- match_score_median が 0.999 まで上がっており、「半分以上のサンプルでほぼ完全一致」を達成。

---

## 5. gpt-5 系の挙動

| 構成 | ディレクトリ | N | compile | match_mean | match_median | valid_rate |
|------|------------|--:|--------:|-----------:|-------------:|-----------:|
| gpt-5 ベースライン | `match_score_n10_6models/` | 10 | 80% | 0.683 | 0.809 | 62.5% |
| gpt-5 + CadQuery docs RAG | `compare_gpt5_n10_rag/` | 10 | 80% | **0.874** | 0.985 | 62.5% |
| gpt-5 N=200 ベースライン | `compare_gpt5_n200/` | 200 | 72.5% | — (旧)<br>iou: 0.851 | iou: 0.996 | 69.0% |

**所見:**
- gpt-5 + CadQuery docs RAG (単独) は match_mean 0.874 と、opus-4-7 両 RAG (0.836) を上回る。
- ただし compile_rate 80%・valid_rate 62.5% と「コンパイル失敗 or verifier 不合格」が多く、**「成功時の品質は高いが安定しない」**プロファイル。
- N=200 の compile_rate 72.5% は N=10 の 80% よりやや低く、母集団を増やすと挙動が悪化するサンプルがあることを示唆。
- 改善案: gpt-5 にも Reference Code RAG を適用 → compile_rate の改善が見込める (要検証)。

---

## 6. 各施策の効果サマリ (opus-4-7 ベース)

| 施策 | 効果 (match_mean) | 効果 (valid_rate) | 備考 |
|------|------------------:|------------------:|------|
| Verify-Correct loop (verifier 弱) | -0.005 | ±0 | 弱 verifier では効果なし |
| Verifier prompt 強化 (v2) | +0.010 | -20pt | critical 検出が厳しくなり valid 率は下がる (正常な挙動) |
| Phase 1 cross-check | +0.007 | +10pt | 微増だが安定 |
| CadQuery docs RAG | (単独効果は gpt-5 で +0.191 確認) | — | API 知識の補強 |
| **Reference Code RAG (hybrid query)** | **+0.099** | **+8.9pt** | 本セッション最大の効果 |
| **累積 (両 RAG + cross-check + verifier v2)** | **+0.111** | — | opus-4-7 で 0.725 → 0.836 |

---

## 7. RAG 実装メモ

### 7.1 CadQuery docs RAG (`backend/app/infrastructure/rag/`)
- ソース: `cadquery_docs/*.md` (workplane / sketch / selectors / apireference 等)
- chunker: ヘディング階層を保持して 1000-trim にチャンク化
- embedding: OpenAI `text-embedding-3-small` + L2 正規化
- 検索: cosine similarity、prompt に top-K を注入
- インデックスディレクトリ: `cadquery_index/`

### 7.2 Reference Code RAG (`reference_corpus.py`, `reference_retriever.py`)
- ソース: DeepCAD `train` split から 10,000 サンプル抽出を目標とし、現状 **992 件構築済み** (時間打ち切り。`scripts/build_reference_corpus.py` は skip-existing 対応なので resume 可能)
- 各エントリの構造:
  - `cadlib_ocp` で JSON → TopoDS_Shape → STEP → CadQuery 正規化
  - **疑似コード化**: 元 `cadlib_ocp` の `__str__` にバグ (`'float' object has no attribute 'round'`) があったため、JSON を直接 walk して CadQuery 風の擬似コードを生成
  - `bbox`、`diameters`、PCD、`fillets`、`chamfers`、`natural_summary` を抽出
- **ハイブリッドクエリ** (Phase 1 の構造化結果 + 特徴名のテキストミックス):
  ```
  bbox=[..] diameters=[..] pcd=[..] fillets=[..] chamfers=[..]
  summary: <自然文サマリ>
  ```
- **リーク防止 3 層**:
  1. データ層: corpus は `train` split のみ (test/val は含めない)
  2. 検索層: `exclude_ids` を呼び出し側で指定し評価対象 ID を除外
  3. 検証層: retrieve 結果に exclude_id が混入していたら hard assert
- 検索結果は `_build_intent_prompt()` で以下のヘッダ下に注入:
  > `## 類似 GT 部品の操作列（参照のみ。同じ操作列を真似して CadQuery で書き直すこと）`

---

## 8. 主要な実装変更

| ファイル | 変更内容 |
|----------|---------|
| `backend/app/infrastructure/rag/reference_corpus.py` | DeepCAD JSON → CadQuery 擬似コードのコンバータ |
| `backend/app/infrastructure/rag/reference_retriever.py` | `ReferenceCodeRetriever` (exclude_ids 対応、hard assert) |
| `backend/app/infrastructure/rag/scripts/build_reference_corpus.py` | corpus 構築スクリプト (10000 目標、skip-existing) |
| `backend/app/infrastructure/rag/scripts/build_reference_index.py` | embedding + L2 正規化、`embeddings.npz` + `entries.json` 保存 |
| `backend/app/infrastructure/vlm/model_factory.py` | `_get_reference_retriever()` singleton、`build_script_generator(exclude_ids=...)` |
| `backend/app/infrastructure/vlm/base/base_script_generator.py` | `_build_intent_prompt()` で両 RAG の retrieve 結果を注入 |
| `backend/app/infrastructure/vlm/anthropic/anthropic_script_generator.py` | `ref_retriever` 受領 |
| `backend/app/infrastructure/vlm/openai/openai_script_generator.py` | `ref_retriever` 受領 + `reasoning_effort="low"` (gpt-5 系で reasoning token を抑制) |
| `backend/app/infrastructure/verification/prompts.py` | P4_SYSTEM の critical 閾値を強化 (silhouette/body count/≥10%scale/axis) |
| `backend/experiments/deepcad/model_comparison.py` | `match_score` 計算、`exclude_ids` 配線、verify-correct ループ統合 |
| UI (`model_factory.py`) | default を opus-4-7 に変更 |

---

## 9. 既知の課題・未解決事項

1. **Reference corpus が 992/10000 件**: コンバータの時間制約で打ち切り。10000 件まで拡張すれば retrieve のヒット精度がさらに向上する見込み (+0.02〜0.05 期待)。
2. **gpt-5 + Reference RAG 未検証**: 「Reference RAG はモデル非依存に効く」を確定するためのクロス検証が未実施。
3. **N=10 は統計的に弱い**: 主結果はすべて N=10。N=200 級の本ベンチで再現性を確認する必要あり。
4. **rollback logic**: Verify-Correct ループで悪化した試行を捨てるロジックが不完全。スコアベースの rollback を導入予定。
5. **Best-of-N 未実装**: 温度をかけた複数生成 + verify_critical + match_score で選択する戦略は未検証。コスト N 倍だが期待効果 +0.05〜+0.10。

---

## 10. 推奨される次の精度向上施策 (優先度順)

1. **Reference corpus を 10,000 件まで拡張** (resume 可能、半自動)
2. **Best-of-N (N=3〜5) の実装** (compile_rate と match_score の両方を底上げ)
3. **gpt-5 にも Reference RAG を適用してクロス検証**
4. **N=200 本ベンチで再現性確認** (opus-4-7 + 両 RAG)
5. **rollback ロジックの修正** (悪化した試行を反映しない)

---

## 11. 最終構成 (本セッション時点)

- **デフォルトモデル**: `claude-opus-4-7`
- **CadQuery docs RAG**: 有効 (`/app/app/infrastructure/rag/cadquery_index/`)
- **Reference Code RAG**: 有効 (`/app/app/infrastructure/rag/reference_index/`, 992 件)
- **Phase 1 cross-check**: 有効
- **Verify-Correct loop**: 有効 (match_score ベースで継続判定)
- **gpt-5 系**: `reasoning_effort="low"` で reasoning token を抑制

この構成での opus-4-7 N=10 ベンチ最終値: **match_score_mean = 0.836** (中央値 0.999、≥0.95 率 55.6%、valid_rate 88.9%)。
