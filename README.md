# WorkoutSavings

A price tracker for protein powder products. Compares prices per 100g and per 100g of protein across brands, tracks price history over time, and supports coupon codes.

**Brands covered:** Prozis, MyProtein, Zumub, Gold Nutrition, Decathlon *(more planned)*

---

## Table of Contents

- [Stack](#stack)
- [Data Model](#data-model)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Running the Project](#running-the-project)
- [Running the Scraper](#running-the-scraper)
- [Project Structure](#project-structure)
- [Firestore Data Structure](#firestore-data-structure)

---

## Stack

| Layer | Technology |
|---|---|
| Backend | Django 5 + Django REST Framework |
| Frontend | React (served by Django) |
| Database | SQLite (dev) |
| Scraper | Selenium + BeautifulSoup + requests |
| Package manager | Poetry |

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

- Python 3.10+
- Poetry
- Google Chrome (for the scraper)

### Steps

```sh
git clone <repository_url>
cd ws-scraper

# Install Python dependencies
poetry install

# Activate the virtual environment
poetry shell
```

---

## Environment Variables

Create a `.env` file in the project root:

```dotenv
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
FIREBASE_CREDENTIALS_PATH=./cred/serviceAccount.json
```

> `FIREBASE_CREDENTIALS_PATH` must point to a valid Firebase service account JSON file.  
> The app will not start without it — Firebase is initialized at startup in `settings_local.py`.

---

## Running the Project

```sh
# Apply migrations
python manage.py migrate

# (Optional) Load seed data
python populate_data.py

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
| `/admin/` | — | Django admin panel |

> **Note:** The `/api/price_history/` endpoint used by the frontend chart is not yet implemented.

---

## Running the Scraper

```sh
# Make sure your virtual environment is active
poetry shell

# Run the scraper (scrapes Prozis and stores to Firestore)
python manage.py scrape_data
```

This runs in two steps:
1. **Link discovery** — searches Prozis for product URLs and saves them to `links/` as JSON files
2. **Data extraction** — opens each product URL and extracts price, flavors, and nutritional info

---

## Project Structure

```
ws-scraper/
├── scraper/                        # Django app
│   ├── models.py                   # Brand, Product, ProductVariant, Price, etc.
│   ├── views.py                    # DRF viewsets
│   ├── serializers.py
│   ├── urls.py
│   ├── tasks.py                    # Scraping logic (Selenium + BeautifulSoup)
│   └── management/
│       ├── commands/
│       │   └── scrape_data.py      # `python manage.py scrape_data`
│       ├── lib_manage_firebase/    # Firebase CRUD helpers
│       └── lib_add_by_hand_firebase/
├── workoutsavings/                 # Django project config
│   ├── settings_local.py           # Active settings (used by manage.py)
│   └── urls.py
├── frontend/                       # React app
│   ├── src/
│   └── build/                      # Compiled and served by Django
├── templates/                      # Django HTML templates
│   └── index.html                  # Loads the React build
├── static/                         # Manually copied React build assets
├── links/                          # Saved product URLs (JSON)
├── cred/                           # Firebase credentials (gitignored)
├── populate_data.py                # Seed script for dev data
├── SCRAPER_STATUS.md               # Detailed scraper health report
├── pyproject.toml
└── .env                            # Local environment variables (gitignored)
```

---

## Firestore Data Structure

The original scraper writes to Firestore. This section documents that structure for reference.

### Collections

**`brands/{brand_name}`**
```
name: string
website: string
product_links/{hash}  →  link, last_updated, category
search_links/{hash}   →  link, last_updated, category
```

**`categories/{category_name}`**
```
name: string
```

**`products/{brand_category_name_weight}`**
```
brand: ref
category: ref
name: string
image_url: string
product_url: string
weight: number (grams)
carbs_percentage: number
fat_percentage: number
protein_percentage: number
is_available: boolean
latest_price/latest  →  price, last_updated
price_history/{id}   →  price, date
```

**`coupons/{coupon_code}`**
```
brand: ref
discount: number
is_percentage: boolean
is_active: boolean
```
