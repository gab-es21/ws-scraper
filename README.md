# WorkoutSavings

A price tracker for protein powder products. Compares prices per 100g and per 100g of protein across brands, tracks price history over time, and supports coupon codes.

**Brands covered:** Prozis *(MyProtein, Zumub and Gold Nutrition planned)*

---

## Table of Contents

- [Stack](#stack)
- [Architecture](#architecture)
- [Data Model](#data-model)
- [Running with Docker](#running-with-docker)
- [Local Development](#local-development)
- [Environment Variables](#environment-variables)
- [API Endpoints](#api-endpoints)
- [Project Structure](#project-structure)

---

## Stack

| Layer | Technology |
|---|---|
| Backend | Django 5.2 + Django REST Framework, gunicorn |
| Frontend | React 19 + Vite, served by nginx |
| Database | PostgreSQL 17 (Docker) / SQLite (local dev) |
| Scraper | requests + BeautifulSoup (JSON-LD) |
| Runtime | Docker Compose |

---

## Architecture

```
            ┌──────────────────── docker compose ────────────────────┐
            │                                                        │
 browser ──►│  web (nginx :8070)                                     │
            │    ├── /            → React build                      │
            │    └── /api /admin  → api (Django + gunicorn :8000)    │
            │                           │                            │
            │  scraper (one-off job) ───┤                            │
            │                           ▼                            │
            │                      db (PostgreSQL, volume pgdata)    │
            └────────────────────────────────────────────────────────┘
```

`api` and `scraper` run the same backend image; `scraper` only starts when invoked.

---

## Data Model

```
Store ─┐
Brand ─┴─► Product ─► Variant (flavor, size_g, gtin)
                         │
                         └─► Listing (store, store_sku, url, is_active)
                                ├─► PriceRecord      price, list_price, in_stock
                                └─► NutritionRecord  protein / carbs / fat per 100 g

Coupon (store, code, discount %)        ScrapeRun (store, status, counts, log)
```

**History stores changes only.** Each scrape compares the scraped values with the
current `PriceRecord` / `NutritionRecord` of the listing:

- same values → only `last_checked_at` is updated
- different values → the current record gets `valid_to = now` and a new record starts with `valid_from = now`

So each row is a period during which the price (or nutrition) stayed the same, and
`valid_from` is exactly when a change was first seen. The logic lives in
`backend/scraper/recording.py`.

€/100g and €/100g of protein are computed from the current price, the variant's size
and the current nutrition (`price_per_100g`, `price_per_100g_protein` in `models.py`).

---

## Running with Docker

Requirements: Docker with Compose v2.

```sh
cp .env.example .env              # then set DJANGO_SECRET_KEY and POSTGRES_PASSWORD

docker compose up -d --build      # db + api + web → http://localhost:8070
docker compose exec api python manage.py createsuperuser   # admin at /admin/

docker compose run --rm scraper   # run the scraper once
docker compose logs -f api        # follow logs
docker compose down               # stop (data stays in the pgdata volume)
```

The `Makefile` has shortcuts for these: `make up`, `make scrape`, `make superuser`, `make logs`, `make down`.

---

## Local Development

Requirements: Python 3.11+, Node 20.19+.

**Backend** (SQLite, no Docker needed):

```sh
python -m venv .venv
.venv\Scripts\activate            # Windows (Linux/macOS: source .venv/bin/activate)
pip install -r backend/requirements-dev.txt

cd backend
python manage.py migrate
python manage.py runserver        # http://127.0.0.1:8000

pytest                            # tests
flake8 .                          # lint
```

**Frontend** (Vite dev server, proxies `/api` to `runserver`):

```sh
cd frontend
npm install
npm run dev                       # http://localhost:5173
```

**Scraper:**

```sh
cd backend
python manage.py scrape_data --date 2024-06-17               # all saved link files of that date
python manage.py scrape_data --date 2024-06-17 --query whey  # one category
```

The scraper reads product URLs from `backend/links/*.json`, fetches each page with `requests`,
extracts name, price, stock and image from the page's JSON-LD, and saves the result to the database.

---

## Environment Variables

Copy `.env.example` to `.env` in the project root. Docker Compose and Django both read it.

| Variable | Used by | Default |
|---|---|---|
| `DJANGO_SECRET_KEY` | Django | dev-only value locally; **required** in Docker |
| `DEBUG` | local Django | `True` (always `False` in Docker) |
| `ALLOWED_HOSTS` | Django | `127.0.0.1,localhost` |
| `CSRF_TRUSTED_ORIGINS` | Django | empty; set when served on a public domain |
| `POSTGRES_PASSWORD` | Docker | **required** |
| `POSTGRES_DB`, `POSTGRES_USER` | Docker | `workoutsavings` |
| `WEB_PORT` | Docker | `8070` |

Django uses PostgreSQL when `POSTGRES_HOST` is set (Compose sets it) and SQLite otherwise.

---

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/stores/` | GET | List all stores |
| `/api/brands/` | GET | List all brands |
| `/api/products/?brand=<id>` | GET | Products, optionally for one brand |
| `/api/extraction-status/` | GET | Every listing with current price, nutrition and last check time |
| `/api/run-extraction/` | POST | Run the scraper on all saved link files |
| `/admin/` | — | Django admin panel |

> **Note:** The `/api/price_history/` endpoint used by the frontend chart is not yet implemented.

---

## Project Structure

```
ws-scraper/
├── backend/
│   ├── scraper/                    # Django app: models, views, serializers, scraping (tasks.py)
│   │   └── management/commands/
│   │       └── scrape_data.py      # `python manage.py scrape_data`
│   ├── workoutsavings/             # Django project config (settings, urls, wsgi)
│   ├── links/                      # Saved product URLs (JSON)
│   ├── Dockerfile
│   ├── requirements.txt            # Runtime dependencies
│   └── requirements-dev.txt        # + test and lint tools
├── frontend/
│   ├── src/                        # React components
│   ├── index.html, vite.config.js
│   ├── nginx.conf                  # Serves the build, proxies /api and /admin
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
├── Makefile
└── WALKTHROUGH.md                  # How the project works, step by step
```
