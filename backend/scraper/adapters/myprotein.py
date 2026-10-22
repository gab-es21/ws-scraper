"""
Myprotein (myprotein.pt).

discover: the product sitemap, keeping sports-nutrition URLs whose slug looks like protein or
          creatine; the JSON-LD category ('Proteína Whey', 'Creatina', ...) decides in the end.
fetch:    the product page only. Its JSON-LD ProductGroup lists every flavor × size variant with
          SKU, EAN, weight, price, crossed-out price and stock. About a third of the variants have
          no weight there; the page's embedded product data has it as the "Amount" choice
          ("750G - 30servings"). The page has one nutrition table (per 100 g); every ?variation=
          page shows the same one, so it applies to all variants.

The site sends no charset, so pages are decoded as UTF-8 explicitly.
"""

import json
import re

from .base import PageResult, StoreAdapter, nutrition_from_tables, plain, sitemap_urls, size_in_grams
from .jsonld import product_group, scraped_items

BASE = "https://www.myprotein.pt"
SITEMAP_INDEX = f"{BASE}/sitemapindex-product.xml.gz"

SLUG_INCLUDE = re.compile(r"whey|protein|proteina|casein|caseina|isolate|isolada|creatin")
SLUG_EXCLUDE = re.compile(
    r"bar|barra|cookie|brownie|wafer|crisp|snack|spread|creme|pancake|oat|aveia|flapjack|shaker|cereal|chips"
    r"|bites|cake|pudding|pudim|bebida|drink|cafe|coffee|iced|water|agua|gel|jelly|gomas|gummies"
    r"|amostra|sample|saqueta|sachet|sticks|pack"
)
TRACKED_CATEGORIES = ("proteina", "creatina")
# In the page's embedded product data: "sku":17725537,"barcode":"...","inStock":true,...,"choices":[{...}]
VARIANT_CHOICES = re.compile(r'"sku":\s*(\d+),[^{}]*?"choices":\s*(\[\s*(?:\{[^{}]*\}\s*,?\s*)*\])')


class MyproteinAdapter(StoreAdapter):
    slug = "myprotein"
    name = "Myprotein"
    website = BASE

    def discover(self):
        index = self.http.get(SITEMAP_INDEX)
        index.raise_for_status()
        urls = []
        for sitemap in sitemap_urls(index.content):
            response = self.http.get(sitemap)
            response.raise_for_status()
            urls += [url for url in sitemap_urls(response.content) if is_candidate(url)]
        return urls

    def fetch(self, url, skip_nutrition_for=frozenset()):
        page = self.http.get(url)
        if page.status_code in (404, 410):
            return PageResult()
        page.raise_for_status()
        return PageResult(items=parse_product_page(page.content.decode("utf-8", "replace"), url))


def is_candidate(url):
    match = re.search(r"/p/([^/]+)/([^/]+)/", url)
    if not match or match.group(1) != "sports-nutrition":
        return False
    slug = match.group(2)
    return bool(SLUG_INCLUDE.search(slug)) and not SLUG_EXCLUDE.search(slug)


def parse_product_page(html, url):
    group, variants = product_group(html)
    if group is None or not plain(group.get("category")).startswith(TRACKED_CATEGORIES):
        return []
    items = scraped_items(group, variants, url, default_brand="Myprotein", nutrition=nutrition_from_tables(html))
    amounts = variant_amounts(html)
    for item in items:
        if item.size_g is None:
            item.size_g = amounts.get(item.store_sku)
    return items


def variant_amounts(html):
    """{sku: grams} from the "Amount" choice of each variant in the embedded product data."""
    amounts = {}
    for sku, choices in VARIANT_CHOICES.findall(html):
        try:
            choices = json.loads(choices)
        except json.JSONDecodeError:
            continue
        for choice in choices:
            if plain(choice.get("optionKey")) in ("amount", "weight", "size") and sku not in amounts:
                grams = size_in_grams(choice.get("key") or choice.get("title"))
                if grams:
                    amounts[sku] = grams
    return amounts
