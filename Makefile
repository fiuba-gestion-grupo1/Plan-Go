.PHONY: up down build logs restart test

up:
	@docker compose up --build

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
