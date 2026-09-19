#!/usr/bin/env bash
# ============================================================
# Hybrid RAG Engine - Container entrypoint
# Prepares runtime directories, then execs the CMD.
# ============================================================
set -euo pipefail

echo "[entrypoint] Preparing runtime directories..."

mkdir -p /app/data/uploads \
         /app/data/index \
         /app/data/cache \
         /app/data/logs \
         "${HF_HOME:-/home/appuser/.cache/huggingface}"

# Try to pre-download NLTK 'punkt' if not present (offline-safe)
python - <<'PY' || echo "[entrypoint] NLTK punkt download skipped (offline?)"
import nltk, sys
try:
    nltk.data.find("tokenizers/punkt")
    print("[entrypoint] NLTK punkt already present")
except LookupError:
    print("[entrypoint] Downloading NLTK punkt...")
    nltk.download("punkt", quiet=True)
PY

echo "[entrypoint] Starting: $*"
exec "$@"