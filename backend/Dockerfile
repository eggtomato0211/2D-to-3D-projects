# CadQueryの依存関係を解決しやすいMambaforgeを使用
FROM condaforge/mambaforge:latest

WORKDIR /app

# OpenGL / OSMesa / cairo ランタイム（CadQuery の OCP + Phase 2 レンダラが必要とする）
# build-essential: PyOpenGL-accelerate の aarch64 ソースビルド用
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1-mesa-glx libglu1-mesa \
    libosmesa6 libosmesa6-dev \
    libxrender1 libsm6 libxext6 libxrandr2 \
    libcairo2 \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Python 3.11 に固定（pyrender の依存 pyglet 1.x が 3.12 で壊れるため）
# CadQuery 2.4 は 3.10-3.12 サポートなので 3.11 採用
RUN mamba install -y -c cadquery -c conda-forge \
    python=3.11 \
    cadquery=2.4 \
    mesalib \
    fastapi \
    uvicorn \
    python-multipart \
    pydantic-settings \
    && pip install "ezdxf<1" --force-reinstall --no-deps \
    && mamba clean -afy

# その他のライブラリ（OpenAI API、レンダラ依存等）は requirements.txt から
# pyrender → PyOpenGL==3.1.0 を pin するが OSMesaCreateContextAttribs 不在で動かないので
# 後段で PyOpenGL を 3.1.7+ に上書きする必要がある
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir --upgrade --no-deps "PyOpenGL>=3.1.7" \
    && pip install --no-cache-dir --upgrade "networkx>=3"

# pyrender / vedo の OSMesa バックエンド設定
ENV PYOPENGL_PLATFORM=osmesa
ENV LIBGL_ALWAYS_SOFTWARE=1
ENV MESA_GL_VERSION_OVERRIDE=3.3

# アプリケーションコードをコピー
COPY . .

# 開発時はホットリロードを有効にして起動
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]