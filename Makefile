# ============================================================
# Hybrid RAG Engine - Makefile
# ============================================================
.DEFAULT_GOAL := help
SHELL := /bin/bash

# ---------- Variables ----------
IMAGE_NAME    := hybrid-rag-engine
IMAGE_TAG     := latest
CONTAINER     := hybrid-rag-engine
PYTHON        := python
PORT          := 8000

# ============================================================
# Help
# ============================================================
.PHONY: help
help: ## Show this help
@echo "Hybrid RAG Engine - Available targets:"
@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# ============================================================
# Local development
# ============================================================
.PHONY: install
install: ## Install Python dependencies locally
$(PYTHON) -m pip install --upgrade pip
$(PYTHON) -m pip install -r requirements.txt

.PHONY: run
run: ## Run the app locally (uvicorn, dev mode)
$(PYTHON) run.py

.PHONY: run-prod
run-prod: ## Run the app locally (production mode)
uvicorn app.main:app --host 0.0.0.0 --port $(PORT)

# ============================================================
# Docker
# ============================================================
.PHONY: docker-build
docker-build: ## Build the Docker image
docker build -t $(IMAGE_NAME):$(IMAGE_TAG) .

.PHONY: docker-run
docker-run: ## Run the container (requires GOOGLE_API_KEY env)
docker run --rm -it \
--name $(CONTAINER) \
-p $(PORT):8000 \
-e GOOGLE_API_KEY=$$GOOGLE_API_KEY \
-v $$(pwd)/data:/app/data \
-v hf-cache:/home/appuser/.cache/huggingface \
$(IMAGE_NAME):$(IMAGE_TAG)

.PHONY: up
up: ## Start with docker-compose (detached)
docker compose up -d --build

.PHONY: down
down: ## Stop docker-compose services
docker compose down

.PHONY: logs
logs: ## Tail docker-compose logs
docker compose logs -f

.PHONY: clean
clean: ## Remove local caches and runtime data
rm -rf data/cache/* data/index/* data/uploads/* data/logs/*
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
rm -rf .pytest_cache .mypy_cache .ruff_cache

.PHONY: docker-clean
docker-clean: ## Remove image and dangling volumes
-docker rm -f $(CONTAINER) 2>/dev/null || true
-docker rmi $(IMAGE_NAME):$(IMAGE_TAG) 2>/dev/null || true
-docker volume rm hf-cache 2>/dev/null || true