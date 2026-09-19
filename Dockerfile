# syntax=docker/dockerfile:1.7
# ============================================================
# Hybrid RAG Engine - Production Dockerfile (CPU only)
# ============================================================
# Multi-stage build optimized for size and build cache
# Base: python:3.11-slim-bookworm
# ============================================================

# ---------- Stage 1: Builder ----------
FROM python:3.11-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Install build deps for native extensions (faiss, PyMuPDF, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        g++ \
        python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install all Python dependencies into a virtual env we can copy
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# ---------- Stage 2: Runtime ----------
FROM python:3.11-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PATH="/opt/venv/bin:$PATH" \
    # HuggingFace cache (mount as volume in compose)
    HF_HOME=/home/appuser/.cache/huggingface \
    TRANSFORMERS_CACHE=/home/appuser/.cache/huggingface/transformers \
    SENTENCE_TRANSFORMERS_HOME=/home/appuser/.cache/huggingface/sentence-transformers \
    # App environment
    HOST=0.0.0.0 \
    PORT=8000 \
    DEBUG=false

# Install runtime system deps:
#   tesseract-ocr       -> OCR for images
#   tesseract-ocr-eng   -> English lang data
#   libgl1, libglib2.0-0 -> required by Pillow / opencv-like libs
#   libgomp1            -> required by faiss / torch
#   curl                -> healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-eng \
        libgl1 \
        libglib2.0-0 \
        libgomp1 \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd --system --gid 1000 appuser && \
    useradd  --system --uid 1000 --gid appuser --create-home --shell /bin/bash appuser

# Copy the virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set working directory
WORKDIR /app

# Copy application code with correct ownership
COPY --chown=appuser:appuser . .

# Create runtime directories and make entrypoint executable
RUN mkdir -p /app/data/uploads /app/data/index /app/data/cache /app/data/logs \
             /home/appuser/.cache/huggingface && \
    chown -R appuser:appuser /app/data /home/appuser/.cache && \
    chmod +x /app/scripts/entrypoint.sh || true

# Drop to non-root
USER appuser

# Expose the FastAPI port
EXPOSE 8000

# Health check hits the lightweight /health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

# Entrypoint prepares runtime dirs, then runs the app
ENTRYPOINT ["/app/scripts/entrypoint.sh"]

# Default command (can be overridden)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]