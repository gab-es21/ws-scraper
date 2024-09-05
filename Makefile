include .env
export

runserver:
	python manage.py runserver

tests:
	python manage.py test

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

populate:
	python populate_data.py
all:
	rm db.sqlite3
	rm ./scraper/migrations/0001_initial.py
	python manage.py makemigrations
	python manage.py migrate
	python manage.py createsuperuser
	python populate_data.py
	python manage.py runserver

