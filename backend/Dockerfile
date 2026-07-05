# Stage 1: Builder — install dependencies and warm up lazy imports.
FROM nvidia/cuda:12.0.1-runtime-ubuntu22.04 AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    DEBIAN_FRONTEND=noninteractive \
    TZ=Europe/Istanbul

RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common curl ca-certificates tzdata \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && add-apt-repository -y ppa:deadsnakes/ppa \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
    python3.12 python3.12-dev python3.12-venv \
    && rm -rf /var/lib/apt/lists/*

RUN python3.12 -m ensurepip && python3.12 -m pip install --no-cache-dir uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY app/ ./app/

RUN uv sync --frozen --no-dev

# Force any lazy TensorRT / torch / DALI initialization to happen at build time,
# not when the container starts.
RUN uv run python -c "import torch, torchvision, tensorrt, nvidia.dali"

RUN uv cache clean

# Stage 2: Runtime — copy only the virtual environment and app code.
FROM nvidia/cuda:12.0.1-runtime-ubuntu22.04 AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    TZ=Europe/Istanbul

RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common curl ca-certificates tzdata \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && add-apt-repository -y ppa:deadsnakes/ppa \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
    python3.12 python3.12-venv \
    && rm -rf /var/lib/apt/lists/*

RUN python3.12 -m ensurepip && python3.12 -m pip install --no-cache-dir uv

RUN useradd -m appuser

WORKDIR /app

COPY --chown=appuser:appuser --from=builder /app/.venv /app/.venv
COPY --chown=appuser:appuser --from=builder /app/pyproject.toml /app/pyproject.toml
COPY --chown=appuser:appuser --from=builder /app/uv.lock /app/uv.lock
COPY --chown=appuser:appuser --from=builder /app/app /app/app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=5 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uv", "run", "uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
