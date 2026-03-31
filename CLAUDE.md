# CLAUDE.md

このファイルはClaude（AI）がblueprint-to-cadリポジトリで作業する際のガイドラインです。

---

## プロジェクト概要

2D工業図面（ラスタ画像）→ VLMによる設計手順の言語化 → CadQuery（Pythonスクリプト）→ 3D B-Repモデル の自動変換パイプライン。

**重要な設計思想：** 画像から直接パラメータを推定するのではなく、「言語化」という中間ステップを挟む。この解釈ステップを省略・スキップしないこと。

---

## よく使うコマンド

```bash
# コンテナ起動
docker-compose up --build

# テスト全実行
docker compose run --rm test

# 特定ファイルのテスト
docker compose run --rm test python -m pytest tests/domain/test_blueprint.py -v
```

---

## アーキテクチャ

クリーンアーキテクチャを採用。依存の方向は必ず外側から内側へ。

```
Presentation → Usecase → Domain ← Infrastructure
```

- **Domain層** はフレームワーク・外部サービスに依存しない純粋なPythonのみ
- **Infrastructure層** にOpenAI/Anthropic APIクライアント・CadQuery実行・ファイルストレージの実装を置く
- VLMモデルやCADエンジンを差し替える場合はInfrastructure層のみ変更する

```
backend/app/
├── presentation/    # FastAPI routers（HTTPの詳細はここに閉じ込める）
├── usecase/         # パイプライン制御ロジック
├── domain/          # エンティティ・外部サービスのインターフェース定義
└── infrastructure/  # 外部サービスの具体的な実装
```

---

## パイプラインの構造

コードを読む・書く際は以下のフェーズを意識すること。

**Phase 1: Generation**
1. VLMが図面を読み取りモデリング手順を言語化（Step 1）
2. 言語化された手順をCadQueryスクリプトに変換（Step 2）
3. スクリプト実行。コンパイルエラー時は自動修正ループ（Step 3）

**Phase 2: Verification & Correction**
4. 3Dモデルを4方向（Top / Front / Side / Iso）からレンダリング（Step 4）
5. 元図面とレンダリング画像を比較し不一致を特定（Step 5）
6. 不一致を修正指示に変換してコードを再生成（Step 6、ループ）

> ⚠️ Phase 2（Multi-View Verification）は現在設計中。実装前に仕様を確認すること。

---

## 技術スタック

| 領域 | 技術 |
|------|------|
| Backend | FastAPI, Python 3.12+, Pydantic |
| Frontend | Next.js (React), Tailwind CSS |
| CAD | CadQuery (Open CASCADE) |
| VLM/LLM | GPT-4o, Claude 3.5 Sonnet |
| インフラ | Docker, Docker Compose |

---

## コーディング規約

- Python は **3.12+** の機能を使ってよい
- 型ヒントを必ず付ける（Pydanticモデルも積極的に活用）
- Domain層のエンティティ・インターフェースを変更する場合は必ずテストを書く
- `backend/app/domain/` 配下に `import fastapi` や `import openai` などを書かない

---

## やってはいけないこと

- Domain層にインフラ依存のコードを書く（FastAPI, OpenAI SDK, CadQuery等のimport禁止）
- エラー修正ループの上限回数を撤廃する（無限ループになる）
- Phase 2の仕様が固まっていない部分を勝手に実装する
- `.env` ファイルをコミットする（APIキーが含まれる）

---

## 環境変数

`.env.example` を参照。最低限以下が必要。

```
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
```

---

## サービスURL（ローカル）

| サービス | URL |
|----------|-----|
| Backend API | http://localhost:8000 |
| Frontend | http://localhost:3000 |
| Swagger UI | http://localhost:8000/docs |