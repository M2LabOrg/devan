.PHONY: setup start stop restart logs shell build

## First-time setup: choose model, build image, pull model
setup:
	@bash setup.sh

## Start the application (and Ollama) in the background
start:
	docker compose up -d
	@echo ""
	@echo "App running at http://localhost:5001"
	@echo "Run 'make logs' to follow output."

## Stop all containers
stop:
	docker compose down

## Restart the app container only (without re-pulling the model)
restart:
	docker compose restart app

## Follow app logs
logs:
	docker compose logs -f app

## Rebuild the image (after code changes)
build:
	docker compose build

## Open a shell inside the running app container
shell:
	docker compose exec app /bin/bash
