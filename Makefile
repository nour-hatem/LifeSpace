SHELL := /bin/bash
export UV_PYTHON_DOWNLOADS := never

API := apps/api
WEB := apps/web

.PHONY: doctor env db-up db-down db-reset lock api-setup api-lint api-format \
	api-typecheck api-test migrate migrate-down dev-api web-setup web-lint \
	web-format web-typecheck web-test web-build dev-web

doctor:
	bash scripts/doctor.sh

env:
	@if [ -f .env ]; then \
		echo ".env already exists; left unchanged"; \
	else \
		cp .env.example .env; \
		echo "created .env from .env.example"; \
	fi

db-up:
	docker compose up -d --wait

db-down:
	docker compose down

db-reset:
	@read -r -p "This deletes all local database data. Continue? [y/N] " answer; \
	case "$$answer" in \
		y|Y) docker compose down -v && docker compose up -d --wait ;; \
		*) echo "aborted; nothing was deleted" ;; \
	esac

lock:
	uv lock --project "$(API)"

api-setup:
	uv sync --project "$(API)" --locked

api-lint:
	cd "$(API)" && uv run ruff check .
	cd "$(API)" && uv run ruff format --check .
	cd "$(API)" && uv run lint-imports

api-format:
	cd "$(API)" && uv run ruff format .

api-typecheck:
	cd "$(API)" && uv run mypy

api-test:
	cd "$(API)" && uv run pytest

migrate:
	uv run --project "$(API)" alembic -c "$(API)/alembic.ini" upgrade head

migrate-down:
	uv run --project "$(API)" alembic -c "$(API)/alembic.ini" downgrade base

dev-api:
	uv run --project "$(API)" uvicorn --factory lifespace.main:create_app --reload --reload-dir "$(API)/src" --host 127.0.0.1 --port 8000

web-setup:
	cd "$(WEB)" && env -u NODE_ENV npm ci

web-lint:
	cd "$(WEB)" && npm run lint
	cd "$(WEB)" && npm run format:check

web-format:
	cd "$(WEB)" && npm run format

web-typecheck:
	cd "$(WEB)" && npm run typecheck

web-test:
	cd "$(WEB)" && npm test

web-build:
	cd "$(WEB)" && npm run build

dev-web:
	cd "$(WEB)" && npm run dev
