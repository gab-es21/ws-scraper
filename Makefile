-include .env
export

runserver:
	python manage.py runserver

tests:
	pytest

lint:
	flake8 .

migrate:
	python manage.py migrate

migrations:
	python manage.py makemigrations

superuser:
	python manage.py createsuperuser

collectstatic:
	python manage.py collectstatic

shell:
	python manage.py shell
