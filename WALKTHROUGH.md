# Project Walkthrough — WorkoutSavings Scraper

> A visual guide to understand what this project is, how it works today,
> what's broken, and where it should go.

---

## 1. What Is This Project?

A **price tracker** for protein powder products (Prozis, eventually others).

The goal:
- Scrape product prices daily from e-commerce sites
- Store prices over time to track history
- Show a frontend where you can compare products by **€/100g** and **€/100g of protein**

---

## 2. Original Vision (Firebase)

This is how the project was **meant to work**:

```
┌─────────────────────┐
│   Prozis website    │  ← scrape product pages
└────────┬────────────┘
         │ Python scraper (requests + BeautifulSoup)
         ▼
┌─────────────────────┐
│   Firebase          │  ← store data (Firestore)
│   Firestore DB      │
└────────┬────────────┘
         │ Firebase JS SDK (direct)
         ▼
┌─────────────────────┐
│   React Frontend    │  ← show prices, charts, comparisons
└─────────────────────┘

Daily run: Cloud Scheduler / GitHub Actions cron
```

Firebase handles both **storage AND the API** — no server needed in between.

---

## 3. How It Actually Works Today

During development, the project was converted to Django + SQLite.
**This is not the original vision:**

```
┌─────────────────────┐
│   Prozis website    │
└────────┬────────────┘
         │ requests + BeautifulSoup
         ▼
┌─────────────────────┐
│  scraper/tasks.py   │  ← extraction logic
└────────┬────────────┘
         │ Django ORM (save_to_db)
         ▼
┌─────────────────────┐
│  SQLite database    │  ← db.sqlite3 (local file)
│  (db.sqlite3)       │
└────────┬────────────┘
         │ Django REST Framework
         ▼
┌─────────────────────┐
│  Django API         │  ← localhost:8000/api/...
└────────┬────────────┘
         │ axios (proxy to port 8000)
         ▼
┌─────────────────────┐
│  React Frontend     │  ← localhost:3000
└─────────────────────┘
```

**Problem:** Django + SQLite adds complexity without adding value if Firebase is the intended backend.

---

## 4. The Scraper — Step by Step

The scraper runs in two phases: **collect links**, then **extract data**.

### Phase 1 — Collect Links (manual / separate script)

Product URLs are saved into JSON files in the `links/` folder:

```
links/
  prozis_whey_pt_links_2024-06-17.json       ← 48 URLs
  prozis_creatine_pt_links_2024-06-17.json   ← N URLs
  prozis_caseina_pt_links_2024-06-17.json    ← N URLs
  prozis_vegan_protein_pt_links_2024-06-17.json
```

Each file is a JSON array of Prozis product URLs:
```json
[
  "https://www.prozis.com/pt/pt/prozis/100-real-whey-protein-1000-g?label=...",
  "https://www.prozis.com/pt/pt/prozis/100-whey-hydro-isolate-2000-g?label=...",
  ...
]
```

### Phase 2 — Extract Product Data

For each URL, `extract_product_jsonld()` in `tasks.py` does 3 HTTP requests:

```
Step 1: GET https://prozis.com/pt/pt/prozis/{slug}
        ↓
        Returns: HTML page with JSON-LD embedded
        Extracts: name, price, brand, SKU, image, availability
        Also: session cookies set, group_id found in page JS

Step 2: GET /pt/pt/product/index?_id={group_id}
        ↓
        Returns: product context JSON (544KB)
        Purpose: sets session context so nutrition API works

Step 3: GET /pt/pt/product/nutrition-table?_id={group_id}&sku={sku}
        ↓
        Returns: nutrition table JSON
        Extracts: protein_g, fat_g, carbs_g per 100g
```

**Why the 3-step chain?** Prozis's nutrition endpoint requires an active session
with cookies from steps 1 and 2. Calling it directly returns 400.

### What JSON-LD Looks Like

Inside every Prozis product page there is a hidden block:

```html
<script type="application/ld+json">
{
  "@type": "Product",
  "name": "100% Real Whey Protein 1000 g",
  "sku": "141765016M01",
  "brand": { "name": "Prozis" },
  "image": "//static.prozis.com/...",
  "offers": {
    "price": "37.99",
    "priceCurrency": "EUR",
    "availability": "http://schema.org/InStock"
  }
}
</script>
```

This is reliable and doesn't break when Prozis redesigns their UI.

### Scraper Output (example run)

```
Processing prozis_whey_pt_links_2024-06-17.json (48 links)
  > 100-real-whey-protein-1000-g  OK  37.99 EUR  [P:74g F:5.2g C:8.8g]
  > 100-whey-hydro-isolate-2000-g OK  125.99 EUR [P:81g F:2.1g C:4.5g]
  > xtreme-whey-protein-ss-2000-g HTTP 404  FAIL
  ...
Done: 40 extracted, 8 failed
```

---

## 5. The Data Model

```
Brand
  └── Product (name, image_url, product_url, is_available)
        └── ProductVariant (Product × Flavor × Quantity)
              ├── NutritionalValue  (protein_%, fat_%, carbs_% per 100g)
              ├── Price             (normal_price, last_updated)
              └── HistoricalPrice   (price + date, one row per day)

Flavor   → e.g. "Chocolate", "Vanilla", or "default" if not tracked
Quantity → weight in grams (e.g. 1000g, 2000g)
Coupon   → discount code per Brand
```

**Example: one product in the DB**

```
Brand:   Prozis
Product: 100% Real Whey Protein 1000 g
  └── ProductVariant: flavor=default, quantity=1000g
        ├── NutritionalValue: protein=74g, fat=5.2g, carbs=8.8g
        ├── Price: €37.99 (updated 2026-05-23)
        └── HistoricalPrice: [€35.99 on 2024-06-17, €37.99 on 2026-05-23]
```

**Computed properties on Price:**

| Property | Formula | Example |
|---|---|---|
| `price_per_100g` | `price / (weight_g / 100)` | 37.99 / 10 = €3.80 |
| `price_per_100g_protein` | `price_per_100g / (protein% / 100)` | 3.80 / 0.74 = €5.13 |

---

## 6. API Endpoints (Django)

### Working

| Method | URL | What it returns |
|---|---|---|
| GET | `/api/brands/` | List of all brands |
| GET | `/api/products/?brand=<id>` | Products filtered by brand |
| GET | `/api/prices/` | All current prices |
| GET | `/api/extraction-status/` | Table: product + price + nutrition + last extracted |
| POST | `/api/run-extraction/` | Triggers scraper on all link files, saves to DB |
| GET | `/admin/` | Django admin panel |

### Broken / Missing

| Method | URL | Status |
|---|---|---|
| POST | `/api/price_history/` | **Missing** — referenced by frontend, never implemented |

---

## 7. The Frontend

Two tabs, served by React (dev: port 3000, prod: built into Django static files):

### Tab 1 — Extraction (default)

```
┌─────────────────────────────────────────────────────────────┐
│ Extraction Status                    [Run Extraction]        │
├────────┬──────────────────┬────────┬───────┬────────────────┤
│ Brand  │ Product          │ Weight │ Price │ Protein | ...  │
├────────┼──────────────────┼────────┼───────┼────────────────┤
│ Prozis │ 100% Real Whey.. │ 1000g  │ 37.99 │   —    | ...  │
│ Prozis │ 100% Whey Hydro  │ 2000g  │125.99 │   —    | ...  │
│  ...   │       ...        │  ...   │  ...  │  ...   | ...  │
└────────┴──────────────────┴────────┴───────┴────────────────┘

Columns: Brand / Product / Weight / Price (€) / €/100g /
         Protein/100g / Carbs/100g / Fat/100g /
         Available (badge) / Last Extracted / Link
```

- "Run Extraction" calls `POST /api/run-extraction/` → scrapes all link files → saves to DB → refreshes table
- Nutrition shows `—` until a successful extraction with nutrition data runs
- Rows marked **(stale)** in orange if last extraction was >7 days ago

### Tab 2 — Dashboard

```
┌─────────────────────────────────────────┐
│ Brand: [-- Select brand --  ▼]          │
│                                         │
│ Products: (hold Ctrl for multiple)      │
│ [ 100% Real Whey Protein 1000 g      ]  │
│ [ 100% Whey Hydro Isolate 2000 g     ]  │
│ [ ...                                ]  │
│                                         │
│ [Show Price History]                    │
└─────────────────────────────────────────┘

↓ (after clicking button)

[Price history chart — currently broken, /api/price_history/ missing]
```

---

## 8. How to Run It Locally

```bash
# 1. Start Django backend
cd ws-scraper
python manage.py runserver        # → http://localhost:8000

# 2. Start React frontend (dev mode)
cd frontend
npm start                         # → http://localhost:3000

# 3. Open Django Admin (manage products, prices, coupons)
# First create a superuser if you haven't:
python manage.py createsuperuser
# Then go to: http://localhost:8000/admin

# 4. Run the scraper manually
python manage.py scrape_data                           # all link files from today
python manage.py scrape_data --date 2024-06-17         # specific date
python manage.py scrape_data --date 2024-06-17 --query whey  # filter by category
```

---

## 9. What Is Working vs Broken

| Feature | Status | Notes |
|---|---|---|
| Scraping price + name + brand | **Working** | JSON-LD extraction is reliable |
| Scraping nutrition (protein/fat/carbs) | **Partial** | Logic exists, blocked by Prozis rate limiting during tests |
| Saving to SQLite (Django ORM) | **Working** | 35 products in DB |
| `GET /api/extraction-status/` | **Working** | Returns all products with prices |
| `POST /api/run-extraction/` | **Working** | Triggers scraper from UI |
| Django Admin `/admin/` | **Working** | All models registered |
| Price history chart (Dashboard tab) | **Broken** | `/api/price_history/` endpoint missing |
| Firebase writing | **Dormant** | Code exists in `lib_manage_firebase/`, not wired to scraper |
| Daily scheduling | **Missing** | No cron, GitHub Actions, or Cloud Scheduler set up |

---

## 10. Firebase Code That Already Exists

The original Firebase writing code is dormant in:

```
scraper/management/
  lib_manage_firebase/
    firebase_setup.py   ← initializes Firebase Admin + Firestore client
    products.py         ← add_or_update_product(), writes price history
    brands.py           ← manage brands in Firestore
    coupons.py          ← manage coupons
    categories.py       ← manage categories
    links.py            ← manage product link URLs

  lib_add_by_hand_firebase/
    manage_products.py  ← manual product entry scripts
    manage_brands.py
    manage_coupons.py
    manage_links.py
```

`products.py` already has the full logic:
- Creates/updates product in Firestore
- Updates `latest_price` subcollection
- Adds to `price_history` subcollection (one entry per day, no duplicates)

**This code is not currently called by the scraper.** `save_to_db()` in `tasks.py`
uses Django ORM instead.

---

## 11. The Two Paths Forward

### Path A — Firebase (original vision)

```
tasks.py (extraction)
    │
    └──► save_to_firebase()        ← restore lib_manage_firebase/products.py
              │
              ▼
        Firestore DB
              │
    ┌─────────┴──────────┐
    │                    │
    ▼                    ▼
React Frontend      Any API consumer
(Firebase JS SDK)   (Firestore REST API)

Scheduling: GitHub Actions cron (free)
Management: Firebase Console + custom React admin section
```

**Pros:** No server to maintain, scales automatically, original design  
**Cons:** Lose Django Admin, need to build management UI in React

---

### Path B — Django properly (current direction)

```
tasks.py (extraction)
    │
    └──► save_to_db()              ← current (keep)
              │
              ▼
        PostgreSQL DB             ← swap SQLite → PostgreSQL
              │
              ▼
        Django API + Admin        ← full management via /admin
              │
              ▼
        React Frontend

Scheduling: Celery + Redis, or a simple cron on the server
Management: Django Admin (already works)
```

**Pros:** Django Admin is powerful and free, price history works naturally, everything in one place  
**Cons:** Needs a server running Django, more infrastructure

---

## 12. Firestore Data Structure (if going Path A)

```
firestore/
  brands/
    prozis/            ← document: { name, logo_url }
      product_links/   ← subcollection of URLs to scrape

  categories/
    whey_protein/      ← document: { name }
    creatine/
    ...

  products/
    prozis_100_real_whey_protein_1000_g/    ← document:
      {                                        name, brand (ref),
        name, brand, category,                 category (ref),
        image_url, product_url,                weight, is_available,
        weight, protein_%, fat_%, carbs_%,     protein/fat/carbs %
        is_available
      }
      latest_price/
        latest/        ← { price: 37.99, last_updated: ... }
      price_history/
        2024-06-17/    ← { price: 35.99, date: "2024-06-17" }
        2026-05-23/    ← { price: 37.99, date: "2026-05-23" }
```

---

*Last updated: 2026-05-23*
