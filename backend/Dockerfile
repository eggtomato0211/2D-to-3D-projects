# CadQueryの依存関係を解決しやすいMambaforgeを使用
FROM condaforge/mambaforge:latest

WORKDIR /app

# CadQueryと主要なライブラリをConda経由でインストール
# (pipで入れるよりOpen CASCADE周りの依存解決が安定します)
# mesalib: OpenGLランタイム（apt不要）
RUN mamba install -y -c cadquery -c conda-forge \
    cadquery=2.4 \
    mesalib \
    fastapi \
    uvicorn \
    python-multipart \
    pydantic-settings \
    && mamba clean -afy

# その他のライブラリ（OpenAI API等）はrequirements.txtから
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY . .

# 開発時はホットリロードを有効にして起動
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]