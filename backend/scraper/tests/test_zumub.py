"""Zumub adapter, against pages shaped like the real ones (trimmed to the parts used)."""

import json
from decimal import Decimal

from scraper.adapters.zumub import BASE, CATEGORY_PAGES, ZumubAdapter, listed_products, parse_product_page

from .fakes import FakeHttp, FakeResponse

URL = f"{BASE}/proteinas/whey/100-whey-gold-standard"


def listing(*urls):
    collection = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "mainEntity": {"@type": "ItemList", "itemListElement": [{"@type": "ListItem", "url": u} for u in urls]},
    }
    return f'<script type="application/ld+json">{json.dumps(collection)}</script>'


def size_variant(sku, name, size, price, list_price=None, in_stock=True):
    offer = {
        "@type": "Offer",
        "price": price,
        "priceCurrency": "EUR",
        "availability": "https://schema.org/InStock" if in_stock else "https://schema.org/OutOfStock",
    }
    if list_price:
        offer["priceSpecification"] = {
            "@type": "UnitPriceSpecification",
            "priceType": "https://schema.org/ListPrice",
            "price": list_price,
        }
    return {"@type": "Product", "name": name, "sku": sku, "size": size, "gtin13": f"56{sku}", "offers": offer}


PRODUCT = {
    "@context": "https://schema.org",
    "@type": "ProductGroup",
    "name": "100% Whey Gold Standard 454g",
    "productGroupID": "9001",
    "variesBy": ["https://schema.org/size"],
    "brand": {"@type": "Brand", "name": "Optimum Nutrition"},
    "category": "Whey",
    "image": "https://www.zumub.com/images/large/on_gold_standard.jpg",
    "hasVariant": [
        size_variant("9001", "100% Whey Gold Standard 454g", "450 g", "34.99"),
        size_variant("9002", "100% Whey Gold Standard 2kg", "2,02kg", "124.00", list_price="139.99"),
        size_variant("9003", "100% Whey Gold Standard 4.5kg", "4.5kg", "244.99", in_stock=False),
    ],
}

PAGE = f"""<html><head><script type="application/ld+json">{json.dumps(PRODUCT)}</script></head><body>
<table><tr><td>Referência</td><td>1ZUM9399</td></tr></table>
<table>
  <tr><th></th><th>Por 31 g</th><th>% Valor Diário</th></tr>
  <tr><td>Energia</td><td>120 kcal</td><td>6%</td></tr>
  <tr><td>Fat</td><td>1.4 g</td><td>2%</td></tr>
  <tr><td>of which saturated</td><td>0.8 g</td><td>4%</td></tr>
  <tr><td>Hidratos de carbono</td><td>1.6 g</td><td>1%</td></tr>
  <tr><td>Proteína</td><td>24 g</td><td>*</td></tr>
</table></body></html>"""


def test_listing_reads_the_json_ld_item_list():
    html = listing(f"{BASE}/proteinas/whey/a", f"{BASE}/proteinas/whey/b")
    assert listed_products(html) == [f"{BASE}/proteinas/whey/a", f"{BASE}/proteinas/whey/b"]


def test_discover_follows_pages_until_nothing_new_and_skips_duplicates():
    a, b, c = (f"{BASE}/proteinas/whey/{x}" for x in "abc")
    whey_pages = {None: listing(a, b, a), 2: listing(c), 3: listing(c)}  # page 3 repeats page 2
    routes = {category: FakeResponse(200, listing()) for category in CATEGORY_PAGES}
    routes[CATEGORY_PAGES[0]] = lambda params: FakeResponse(200, whey_pages[(params or {}).get("page")])
    routes[f"{BASE}/creatina"] = FakeResponse(200, listing(a, f"{BASE}/creatina/d"))
    http = FakeHttp(routes)

    assert ZumubAdapter(http=http).discover() == [a, b, c, f"{BASE}/creatina/d"]
    whey_requests = [params for url, params in http.requests if url == CATEGORY_PAGES[0]]
    assert whey_requests == [None, {"page": 2}, {"page": 3}]


def test_product_page_gives_one_item_per_size():
    small, medium, large = parse_product_page(PAGE, URL)

    assert (small.brand, small.product_name, small.category) == ("Optimum Nutrition", "100% Whey Gold Standard", "Whey")
    assert (small.store_sku, small.flavor, small.size_g, small.gtin) == ("9001", "", Decimal("450"), "569001")
    assert (small.price, small.list_price, small.in_stock) == (Decimal("34.99"), None, True)
    assert (medium.size_g, medium.list_price) == (Decimal("2020"), Decimal("139.99"))
    assert (large.size_g, large.in_stock) == (Decimal("4500"), False)


def test_per_serving_nutrition_is_scaled_to_100g():
    item = parse_product_page(PAGE, URL)[0]

    assert (item.protein_g, item.carbs_g, item.fat_g) == (Decimal("77.42"), Decimal("5.16"), Decimal("4.52"))


def test_page_without_structured_data_yields_nothing():
    assert parse_product_page("<html></html>", URL) == []


def test_fetch_and_gone_products():
    http = FakeHttp({URL: FakeResponse(200, PAGE.encode("utf-8"))})

    assert len(ZumubAdapter(http=http).fetch(URL).items) == 3
    assert ZumubAdapter(http=FakeHttp({})).fetch(URL).items == []
