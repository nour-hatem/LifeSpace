SHELL := /bin/bash
export UV_PYTHON_DOWNLOADS := never

API := apps/api
WEB := apps/web

.DEFAULT_GOAL := help

.PHONY: help setup lint format typecheck test build check smoke \
	doctor env db-up db-down db-reset lock api-setup api-lint api-format \
	api-typecheck api-test api-spec api-spec-check api-types api-types-check \
	migrate migrate-down dev-api web-setup web-lint \
	web-format web-typecheck web-test web-build dev-web

help: ## List available targets
	@awk 'BEGIN {FS = ":.*## "} /^[a-zA-Z0-9_-]+:.*## / {printf "  %-14s %s\n", $$1, $$2}' "$(MAKEFILE_LIST)"

setup: env api-setup web-setup ## Create .env if missing and install both apps
lint: api-lint web-lint ## Lint the backend and frontend
format: api-format web-format ## Format the backend and frontend
typecheck: api-typecheck web-typecheck ## Type-check the backend and frontend
test: api-test web-test ## Run backend and frontend tests
build: web-build ## Build the web application
check: lint typecheck test build ## Run lint, typecheck, tests, and build
smoke: ## Check the running API and web servers
	bash scripts/smoke.sh

doctor: ## Check local prerequisites
	bash scripts/doctor.sh

env: ## Create .env from .env.example when missing
	@if [ -f .env ]; then \
		echo ".env already exists; left unchanged"; \
	else \
		cp .env.example .env; \
		echo "created .env from .env.example"; \
	fi

db-up: ## Start PostgreSQL 18 and wait for it to be healthy
	docker compose up -d --wait

db-down: ## Stop PostgreSQL, keeping its data
	docker compose down

db-reset: ## Delete local database data and recreate the database
	@read -r -p "This deletes all local database data. Continue? [y/N] " answer; \
	case "$$answer" in \
		y|Y) docker compose down -v && docker compose up -d --wait ;; \
		*) echo "aborted; nothing was deleted" ;; \
	esac

lock: ## Resolve and lock Python dependencies
	uv lock --project "$(API)"

api-setup: ## Install backend dependencies from the lockfile
	uv sync --project "$(API)" --locked

api-lint: api-spec-check ## Lint and format-check the backend, and check layer contracts
	cd "$(API)" && uv run ruff check .
	cd "$(API)" && uv run ruff format --check .
	cd "$(API)" && uv run lint-imports

api-spec: ## Export the OpenAPI document to apps/web/src/shared/api/openapi.json
	uv run --project "$(API)" python -m lifespace.openapi_export "$(WEB)/src/shared/api/openapi.json"

api-spec-check: ## Fail when the committed OpenAPI document is stale
	@set -e; \
	tmp=$$(mktemp); \
	trap 'rm -f "$$tmp"' EXIT; \
	uv run --project "$(API)" python -m lifespace.openapi_export "$$tmp"; \
	if ! diff -u "$(WEB)/src/shared/api/openapi.json" "$$tmp"; then \
		echo "OpenAPI spec is out of date. Run: make api-types"; \
		exit 1; \
	fi

api-types: api-spec ## Generate TypeScript types from the OpenAPI document
	cd "$(WEB)" && env -u NODE_ENV npx --yes openapi-typescript@7.13.0 src/shared/api/openapi.json -o src/shared/api/schema.d.ts

api-types-check: ## Fail when the committed TypeScript types are stale
	@set -e; \
	tmp=$$(mktemp --suffix=.d.ts); \
	trap 'rm -f "$$tmp"' EXIT; \
	cd "$(WEB)" && env -u NODE_ENV npx --yes openapi-typescript@7.13.0 src/shared/api/openapi.json -o "$$tmp"; \
	if ! diff -u src/shared/api/schema.d.ts "$$tmp"; then \
		echo "Types are out of date. Run: make api-types"; \
		exit 1; \
	fi

api-format: ## Format the backend with ruff
	cd "$(API)" && uv run ruff format .

api-typecheck: ## Type-check the backend with mypy
	cd "$(API)" && uv run mypy

api-test: ## Run backend unit and integration tests
	cd "$(API)" && uv run pytest

migrate: ## Apply database migrations up to head
	uv run --project "$(API)" alembic -c "$(API)/alembic.ini" upgrade head

migrate-down: ## Revert all database migrations (development only)
	uv run --project "$(API)" alembic -c "$(API)/alembic.ini" downgrade base

dev-api: ## Run the API on 127.0.0.1:8000 with reload
	uv run --project "$(API)" uvicorn --factory lifespace.main:create_app --reload --reload-dir "$(API)/src" --host 127.0.0.1 --port 8000

web-setup: ## Install frontend dependencies from the lockfile
	cd "$(WEB)" && env -u NODE_ENV npm ci

web-lint: ## Lint and format-check the frontend
	cd "$(WEB)" && npm run lint
	cd "$(WEB)" && npm run format:check

web-format: ## Format the frontend with prettier
	cd "$(WEB)" && npm run format

web-typecheck: ## Type-check the frontend with tsc
	cd "$(WEB)" && npm run typecheck

web-test: ## Run frontend tests with Vitest
	cd "$(WEB)" && npm test

web-build: ## Build the frontend for production
	cd "$(WEB)" && npm run build

dev-web: ## Run the Vite dev server on 127.0.0.1:5173
	cd "$(WEB)" && npm run dev
