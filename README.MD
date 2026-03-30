# Blueprint-to-CAD (B2C)

> **VLMを用いた2D工業図面から3Dパラメトリックモデルへの自動変換システム**

2Dの工業図面（ラスタ画像）を解析し、設計意図を自然言語で言語化した上で、CadQuery（Pythonスクリプト）を用いて高精度な3D B-Repモデルを自動生成するシステムです。

---

## 🎯 プロジェクトの概要

製造業における「2D図面から3Dへの書き起こし」作業は、依然として人間の設計者に依存しており、膨大な工数がかかっています。

既存のSOTA（CAD2Program等）は画像から直接パラメータを推定しますが、本プロジェクトでは **「VLMによる設計手順の言語化」** という中間ステップを挟むことで、人間レベルの推論プロセスを再現し、高い解釈性と修正精度を実現します。

### 主な特徴

| 特徴 | 説明 |
|------|------|
| **Design Intent Extraction** | VLMが2dの図面を読み取り、人間が理解可能な「設計手順書」を生成 |
| **Code-based Generation** | LLMと相性の良いCadQueryを採用し、実行可能なPythonコードを出力 |
| **Multi-View Verification** | 生成した3Dモデルを4方向から自動撮影し、元図面との整合性を自己検証・修正 (ここはまだ確実に決まっているわけではない)|
| **Clean Architecture** | FastAPIを用いた堅牢な設計により、VLMモデルやCADエンジンの差し替えが容易 |

---

## 🏗️ システム構成

### アーキテクチャ（Clean Architecture）

バックエンドはPython（FastAPI）で構築され、クリーンアーキテクチャを採用してドメインロジックを技術的な詳細から分離しています。

```
├── Presentation Layer     # FastAPIによるREST API
├── Usecase Layer          # 言語化・コード生成・エラー修正ループの制御
├── Domain Layer           # CADモデル・図面のエンティティ、外部サービスのIF定義
└── Infrastructure Layer   # OpenAI/Anthropic APIクライアント、CadQuery実行環境、ファイルストレージ
```

### 技術スタック

| Layer | Technology |
|-------|------------|
| Frontend | Next.js (React), Tailwind CSS |
| Backend | FastAPI (Python 3.12+), Pydantic |
| CAD Engine | CadQuery (Open CASCADE) |
| VLM / LLM | GPT-4o, Claude 3.5 Sonnet |
| Infrastructure | Docker, Docker Compose |

---

## 🛠️ パイプラインの詳細

### Phase 1: 生成（Generation）

```
Step 1: 言語化
  VLMが図面（三面図とは限らない）を読み取り、モデリング手順をステップバイステップで生成

Step 2: 実装
  言語化された手順をCadQueryスクリプト（Python）に変換

Step 3: 実行
  スクリプトを実行。コンパイルエラー時はエラー文を元に自動修正
```

### Phase 2: 検証・修正（Verification & Correction）

```
Step 4: レンダリング
  生成した3Dモデルを4方向（Top / Front / Side / Iso）から撮影

Step 5: 照合
  元の図面とレンダリング画像を比較し、寸法・形状の不一致を特定

Step 6: フィードバック
  不一致箇所を修正指示に変換し、コードを再生成（ループ）
```

---

## 🚦 Getting Started

### 前提条件

- Docker / Docker Compose がインストールされていること
- OpenAI または Anthropic の APIキーを取得済みであること

### セットアップ

```bash
# リポジトリのクローン
git clone https://github.com/your-username/blueprint-to-cad.git
cd blueprint-to-cad

# 環境変数の設定
cp .env.example .env
# .env を編集して APIキー等を入力

# コンテナの起動
docker-compose up --build
```

| サービス | URL |
|----------|-----|
| Backend API | http://localhost:8000 |
| Frontend | http://localhost:3000 |
| API Docs (Swagger) | http://localhost:8000/docs |

---

## 🧪 テスト

```bash
docker compose run --rm test
```

特定のファイルだけ実行する場合：

```bash
docker compose run --rm test python -m pytest tests/domain/test_blueprint.py -v
```

---

## 📁 ディレクトリ構成（予定）

```
blueprint-to-cad/
├── backend/
│   ├── app/
│   │   ├── presentation/    # FastAPI routers
│   │   ├── usecase/         # ユースケース層
│   │   ├── domain/          # エンティティ・インターフェース
│   │   └── infrastructure/  # 外部サービス実装
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🔗 関連研究

- [CAD2Program](https://arxiv.org/abs/xxxx.xxxxx) - 画像から直接パラメータを推定するSOTA手法
- [cadrile (ICLR 2026)](https://arxiv.org/abs/xxxx.xxxxx) - 比較対象の最新手法
- [CadQuery Documentation](https://cadquery.readthedocs.io/) - 本プロジェクトで使用するCADライブラリ

---
