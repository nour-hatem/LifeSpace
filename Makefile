SHELL := /bin/bash
export UV_PYTHON_DOWNLOADS := never

API := apps/api
WEB := apps/web

.PHONY: doctor env db-up db-down db-reset

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
