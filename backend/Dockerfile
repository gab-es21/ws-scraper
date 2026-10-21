# bookworm (OpenSSL 3.0), not the default trixie (OpenSSL 3.5): Prozis' Cloudflare
# answers 429 to the OpenSSL 3.5 TLS handshake but 200 to OpenSSL 3.0.
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN DJANGO_SECRET_KEY=collectstatic-only python manage.py collectstatic --noinput

RUN useradd --create-home app && chown -R app:app /app
USER app

EXPOSE 8000

# Apply migrations, then serve. The scraper service overrides this command.
CMD ["sh", "-c", "python manage.py migrate --noinput && exec gunicorn workoutsavings.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 60 --access-logfile -"]
