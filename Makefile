.PHONY: up down build logs restart test

up:
	@docker volume rm plan-go_plango_data || true
	@docker compose up --build -d
	@echo "Esperando que la app termine de levantar..."
	@sleep 5
	@docker exec plan-go-app python -m backend.app.seed_users
	@docker exec plan-go-app python -m backend.app.seed_db
	@docker exec plan-go-app python -m backend.app.seed_benefits

down:
	@docker compose down

build:
	@docker compose build --no-cache

logs:
	@docker compose logs -f

restart:
	@docker compose down
	@docker compose up --build -d

test:
	docker compose build test
	docker compose run --rm test
