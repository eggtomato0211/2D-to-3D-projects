FROM condaforge/mambaforge:latest

WORKDIR /app

# OS 依存:
#   - libgl1-mesa-glx / libglu1-mesa: OCP の OpenGL ランタイム
#   - libosmesa6 / libosmesa6-dev: pyrender headless レンダリング
#   - libegl1: 一部の Linux 環境で必要
#   - poppler-utils: pdf2image
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1-mesa-glx libglu1-mesa libosmesa6 libosmesa6-dev libegl1 \
        poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Conda 経由で CadQuery と FastAPI を入れる（pip より OCP の依存解決が安定）
RUN mamba install -y -c cadquery -c conda-forge \
        cadquery=2.4 \
        mesalib \
        fastapi \
        uvicorn \
        python-multipart \
        pydantic-settings \
    && pip install "ezdxf<1" --force-reinstall --no-deps \
    && mamba clean -afy

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
