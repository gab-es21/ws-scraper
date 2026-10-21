-include .env
export

# --- Docker -------------------------------------------------------------

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f

scrape:
	docker compose run --rm scraper

superuser:
	docker compose exec api python manage.py createsuperuser

# --- Local development (backend/ with .venv, frontend/ with npm) ---------

runserver:
	cd backend && python manage.py runserver

frontend:
	cd frontend && npm run dev

tests:
	cd backend && pytest

lint:
	cd backend && flake8 .

migrate:
	cd backend && python manage.py migrate

migrations:
	cd backend && python manage.py makemigrations

shell:
	cd backend && python manage.py shell
