# WorkoutSavings

A price tracker for protein powder products. Compares prices per 100g and per 100g of protein across brands, tracks price history over time, and supports coupon codes.

**Brands covered:** Prozis *(MyProtein, Zumub and Gold Nutrition planned)*

---

## Table of Contents

- [Stack](#stack)
- [Data Model](#data-model)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Running the Project](#running-the-project)
- [Running the Scraper](#running-the-scraper)
- [Project Structure](#project-structure)

---

## Stack

| Layer | Technology |
|---|---|
| Backend | Django 5.2 + Django REST Framework |
| Frontend | React |
| Database | SQLite (dev) |
| Scraper | requests + BeautifulSoup (JSON-LD) |
| Package manager | pip (`requirements.txt`) |

---

## Data Model

```
Brand
  └── Product
        └── ProductVariant  (Product × Flavor × Quantity)
              ├── NutritionalValue  (carbs %, fat %, protein %)
              ├── Price             (current price + price/100g + price/100g protein)
              └── HistoricalPrice   (one entry per scrape run)

Coupon  (linked to Brand)
```

**Prices exposed by the API:**
- Normal price (€)
- Price with promo code (€)
- Price per 100g (with and without promo)
- Price per 100g of protein (with and without promo)

---

## Installation

### Requirements

- Python 3.11+

### Steps

```sh
git clone <repository_url>
cd ws-scraper

python -m venv .venv
.venv\Scripts\activate            # Windows (Linux/macOS: source .venv/bin/activate)
pip install -r requirements-dev.txt
```

---

## Environment Variables

Copy `.env.example` to `.env` in the project root and adjust as needed:

```dotenv
DJANGO_SECRET_KEY=change-me
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
```

Every variable has a development default, so `.env` is optional locally.

---

## Running the Project

```sh
# Apply migrations
python manage.py migrate

# Create a superuser for the admin panel
python manage.py createsuperuser

# Start the development server
python manage.py runserver
```

Open `http://127.0.0.1:8000/` in your browser.

**API endpoints:**

| Endpoint | Method | Description |
|---|---|---|
| `/api/brands/` | GET | List all brands |
| `/api/products/?brand=<id>` | GET | Products for a brand |
| `/api/prices/` | GET | All current prices |
| `/api/extraction-status/` | GET | Products with current price, nutrition and last extraction time |
| `/api/run-extraction/` | POST | Run the scraper on all saved link files |
| `/admin/` | — | Django admin panel |

> **Note:** The `/api/price_history/` endpoint used by the frontend chart is not yet implemented.

**Tests and lint:**

```sh
pytest
flake8 .
```

---

## Running the Scraper

```sh
# Extract all products from the saved link files of a given date
python manage.py scrape_data --date 2024-06-17

# Only one category
python manage.py scrape_data --date 2024-06-17 --query whey
```

The scraper reads product URLs from `links/*.json`, fetches each page with `requests`,
extracts name, price, stock and image from the page's JSON-LD, and saves the result to the database.

---

## Project Structure

```
ws-scraper/
├── scraper/                        # Django app
│   ├── models.py                   # Brand, Product, ProductVariant, Price, etc.
│   ├── views.py                    # DRF viewsets + extraction endpoints
│   ├── serializers.py
│   ├── urls.py
│   ├── tasks.py                    # Scraping logic (requests + JSON-LD)
│   └── management/commands/
│       └── scrape_data.py          # `python manage.py scrape_data`
├── workoutsavings/                 # Django project config (settings, urls, wsgi)
├── frontend/                       # React app
├── templates/index.html            # Loads the React build
├── links/                          # Saved product URLs (JSON)
├── WALKTHROUGH.md                  # How the project works, step by step
├── requirements.txt                # Runtime dependencies
├── requirements-dev.txt            # + test and lint tools
└── .env.example                    # Environment variables template
```
