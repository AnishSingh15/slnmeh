.PHONY: install dev-api dev-web test lint format ingest openapi docker-build docker-run

install:
	cd backend && uv sync
	cd frontend && npm ci

dev-api:
	cd backend && uv run uvicorn --factory winddesk.main:create_app --reload --port 8000

dev-web:
	cd frontend && npm run dev

test:
	cd backend && uv run pytest -q
	cd frontend && npm test

lint:
	cd backend && uv run ruff check . && uv run ruff format --check . && uv run mypy winddesk
	cd frontend && npm run lint && npm run format:check && npm run typecheck

format:
	cd backend && uv run ruff format . && uv run ruff check --fix .
	cd frontend && npm run format

ingest:
	cd backend && uv run python -m winddesk.ingest

openapi:
	cd backend && uv run python -m winddesk.openapi ../frontend/openapi.json
	cd frontend && npm run gen:api

docker-build:
	docker build -t winddesk .

docker-run: docker-build
	docker run --rm -p 8000:8000 winddesk
