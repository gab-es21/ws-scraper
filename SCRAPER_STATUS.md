# Scraper Status Report

> Last tested: **2026-05-23**  
> Target: [Prozis PT](https://www.prozis.com/pt/pt/)  
> Tester: Claude Code (automated)

---

## Summary

| Extractor | Method | Status | Notes |
|---|---|---|---|
| Product page — name, price, image | `requests` + JSON-LD | ✅ **Working** | No Selenium needed |
| Product page — availability, SKU | `requests` + JSON-LD | ✅ **Working** | No Selenium needed |
| Saved product links (June 2024) | `requests` | ✅ **Working** | All 48 URLs still return 200 |
| Product page — nutritional data | Selenium | ❌ **Broken** | Bot detection blocks headless Chrome |
| Product page — flavors/variants | Selenium | ❌ **Broken** | Bot detection blocks headless Chrome |
| Search/listing page — product links | Selenium | ❌ **Broken** | Bot detection + site redesign |
| All old CSS selectors (6/6) | — | ❌ **All dead** | Prozis redesigned their site |
| Django DB read/write | Django ORM | ✅ **Working** | Has seed data, models intact |
| Firestore (current storage) | Firebase | ⚠️ **Untested** | Credentials present, not verified live |

---

## Extractor Details

### ✅ Product Page — JSON-LD (Working)

Prozis embeds a `<script type="application/ld+json">` block on every product page.  
This gives us structured data **without Selenium** — just `requests` + `BeautifulSoup`.

**What we get:**

| Field | Example |
|---|---|
| Name | `100% Real Whey Protein 1000 g` |
| Brand | `Prozis` |
| Price | `37.99 EUR` |
| Availability | `InStock` / `OutOfStock` |
| Image URL | `//static.sscontent.com/...jpg` |
| SKU | `NUT00/1417651710` |

**Sample extracted data:**
```json
{
  "name": "100% Real Whey Protein 1000 g",
  "brand": "Prozis",
  "price": "37.99",
  "currency": "EUR",
  "availability": "InStock",
  "image": "//static.sscontent.com/thumb/400/400/products/124/v1730929_prozis_100-real-whey-protein-1000g_1.jpg",
  "sku": "NUT00/1417651710"
}
```

**Works on all saved links** — tested on 3 of 48 URLs from the June 2024 link files, all returned valid JSON-LD.

---

### ❌ Old CSS Selectors (All Broken)

Prozis has fully redesigned their site. Every selector used by the original scraper is dead.

| Selector | Used for | Status |
|---|---|---|
| `h1.col-10.px-0.product-name.mb-2.mt-0` | Product title | ❌ Dead |
| `#ob-product-price` | Price | ❌ Dead |
| `#carouselPicker` | Flavor/variant carousel | ❌ Dead |
| `#tab_NUTRITION_TABLE` | Nutritional data tab | ❌ Dead |
| `#quick-search_query` | Search input | ❌ Dead |
| `.col.list-item` | Search result items | ❌ Dead |

---

### ❌ Nutritional Data (Broken — Bot Detection)

Nutritional values (protein %, fat %, carbs %) are **not in the static HTML** — they only appear after JavaScript renders the page.

When tested with headless Chrome (Selenium), the page returns an **empty DOM** — no `<h1>` tags, no tables, no product elements. This is consistent with Prozis running **bot/headless browser detection**.

**Impact:** Protein/fat/carb percentages cannot be scraped with the current approach.

**Options to fix:**
- Run Chrome in **non-headless mode** (visible window — works locally, not on servers)
- Use [undetected-chromedriver](https://github.com/ultrafunkamsterdam/undetected-chromedriver) to bypass detection
- Use a service like Browserless or Playwright with stealth plugins
- Manually maintain the nutritional table (it changes rarely)

---

### ❌ Search / Listing Pages (Broken)

The search and category listing pages that the scraper uses to discover product URLs are now a fully **JavaScript-rendered SPA**.

- HTTP `GET` returns a 200 but the product cards are not in the static HTML
- Headless Selenium also returns empty DOM (same bot detection as above)
- The old search URL pattern (`/pt/pt/` + search query via keyboard input) no longer works

**Impact:** Cannot automatically discover new product URLs.

**Workaround available:** The `links/` folder has **48 saved product URLs** from June 2024 that are all still valid. These can be re-scraped immediately.

---

### ✅ Saved Link Files (Working)

The `links/` folder contains 4 JSON files from June 17, 2024 with a total of **48 product URLs**.

| File | Products |
|---|---|
| `prozis_whey_pt_links_2024-06-17.json` | 28 |
| `prozis_vegan_protein_pt_links_2024-06-17.json` | ~10 |
| `prozis_creatine_pt_links_2024-06-17.json` | ~10 |
| `prozis_caseina_pt_links_2024-06-17.json` | ~2 |

All tested URLs return HTTP 200 and have valid JSON-LD. These can be used to run a price extraction **today** without solving the bot detection problem.

---

### ✅ Django DB (Working)

The Django ORM and SQLite database are working correctly.

```
Brands:           5   (Prozis, My Protein, Zumub, Gold Nutrition, Decathlon)
Products:         2   (seed data only — "Whey Protein", "Impact Whey")
ProductVariants:  2
Prices:           2   (frozen at July 2024)
HistoricalPrices: 20  (fake price history)
Coupons:          2   (PROZIS20, MYPROTEIN25)
```

> **Note:** All current data is fake seed data from `populate_data.py`. No real scraping has ever been stored here. The scraper currently writes to **Firestore**, not this DB.

---

## What Needs to Change

### 1. Storage: Firestore → Django DB

`scraper/tasks.py` still calls `db = firestore.client()` and `store_product_data()` which writes to Firestore. This needs to be rewritten to use the Django ORM models (`Brand`, `Product`, `ProductVariant`, `Price`, `HistoricalPrice`).

### 2. Product Extraction: Selenium → `requests` + JSON-LD

The `get_products_info()` and `extract_product_title()` / `extract_product_price()` functions all use broken CSS selectors. They should be replaced with a simple `requests` + JSON-LD parser — faster, more reliable, no browser needed.

### 3. Nutritional Data: New approach needed

Options (see details above). Simplest short-term fix: **non-headless** Selenium for nutritional data only, while using `requests` for everything else.

### 4. Link Discovery: New selectors or manual upkeep

The search step is blocked by bot detection. Short-term: re-use the existing 48 saved links. Long-term: find new selectors or use a stealth browser library.

---

## Recommended Next Steps

```
Priority 1 (quick win)
  → Rewrite product extraction to use requests + JSON-LD
  → Rewrite storage to use Django DB
  → Run extraction on the 48 existing saved links

Priority 2 (fixes data gaps)
  → Solve nutritional data (undetected-chromedriver or manual table)

Priority 3 (new product discovery)
  → Fix link discovery (new selectors or stealth browser)
```
