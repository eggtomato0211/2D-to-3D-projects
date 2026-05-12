# VLM eval — Phase 2 検証エンジン用プロンプト/入力構成の比較実験

「**どんな画像セットとプロンプト構造で VLM に渡せば、生成モデルと参照モデルの差分を正しく検出できるか**」を測る実験。

## 設計

### Case A: 既知バグの故意モデル
正常モデル（reference）と意図的に壊した variant の差分検出を VLM に試させる。
ground truth は手動定義。

| Variant | 何を壊したか | 期待される検出 |
|---|---|---|
| `v1_missing_left_hole` | 左 φ6 穴を削除（穴 2 個に減少） | hole 1 件欠落 (critical) |
| `v2_no_chamfer` | C0.5 全周面取りを削除 | chamfer 欠落 (minor) |
| `v3_no_fillet` | R3 縦エッジフィレットを削除 | fillet 欠落 (major) |

### 評価軸（独立変数）
| 軸 | 候補値 |
|---|---|
| **画像セット** | `IS1_iso_only` (1枚) / `IS2_4_line` (線画 4枚) / `IS3_8_mixed` (線画 4 + 影付き 4) |
| **プロンプト** | `P1_freeform` / `P2_checklist` / `P3_structured_json` |
| **VLM** | `claude-sonnet-4-5` / `gpt-4o`（API キーが揃っていれば両方） |

3 variants × 3 image sets × 3 prompts × 2 models = **最大 54 回**の VLM 呼び出し。

## 実行

`.env` に `ANTHROPIC_API_KEY` と `OPENAI_API_KEY` を設定したうえで:

```bash
# プロジェクトルートから
docker compose --profile vlm-eval run --rm vlm-eval

# dry-run（呼び出し数だけ表示、API は呼ばない）
docker compose --profile vlm-eval run --rm vlm-eval python run_eval.py --dry-run

# 一部だけ走らせる
docker compose --profile vlm-eval run --rm vlm-eval python run_eval.py \
    --only-variant v1_missing_left_hole \
    --only-image-set IS2_4_line \
    --only-prompt P3_structured_json
```

## 出力

```
backend/experiments/vlm_eval/output/
├── images/
│   ├── _reference/
│   │   ├── shaded/{top,front,side,iso}.png   # 影付き raster
│   │   └── line/{top,front,side,iso}.png     # 線画
│   ├── v1_missing_left_hole/{shaded,line}/...
│   ├── v2_no_chamfer/{shaded,line}/...
│   └── v3_no_fillet/{shaded,line}/...
├── results/
│   └── results.json                          # raw VLM 出力
└── summary.html                              # 一覧比較ビュー
```

ホスト側で:
```bash
open backend/experiments/vlm_eval/output/summary.html
```

## 評価の見方

`summary.html` で variant ごとに:
1. 上段: ground truth（人手で定義した期待される検出項目）
2. グリッド: model × prompt × image_set ごとの VLM 出力

**評価ポイント**:
- ground truth に挙げた特徴を正しく拾っているか（recall）
- 余計な「差分っぽい何か」を hallucinate してないか（precision）
- structured JSON プロンプトの場合: スキーマ通りに出力できているか
- model × prompt の組み合わせで応答品質に差があるか

## 拡張

- **画像セット追加**: `run_eval.py` の `IMAGE_SETS` に新エントリ
- **プロンプト追加**: `prompts.py` に追加し `ALL_PROMPTS` に登録
- **モデル追加**: `vlm_clients.py` の `default_clients()` に追加
- **Case B（実図面 RING）への拡張**: `cases.py` の `Variant` を拡張し、外部画像（drawing.png）を持たせる構造にする

## コスト目安

完全実行（54 calls）で:
- 画像 1 枚 ≒ 1500 tokens（1024×1024）として、IS3_8_mixed では 16 枚 → ~24K tokens 入力
- 出力は 500-1500 tokens
- Claude Sonnet 4.5 で約 $0.5-1.5、GPT-4o で約 $0.5-1.0
- 合計 **概算 $1-3 / 完全実行**
