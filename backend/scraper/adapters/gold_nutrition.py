"""
Gold Nutrition (goldnutrition.pt), a Shopify store.

discover: the public /products.json feed (every product with all variants, 250 per page);
          products are kept when their title looks like protein or creatine.
fetch:    served from the feed, no extra request.

Product pages answer 429 to plain HTTP clients, so there is no nutrition table:
nutrition stays empty unless entered in the admin (scrapes never overwrite it).
"""

import re

from ..recording import ScrapedItem
from .base import PageResult, StoreAdapter, plain, size_in_grams, to_decimal

BASE = "https://goldnutrition.pt"
FEED_URL = f"{BASE}/products.json"
PAGE_SIZE = 250

INCLUDE = re.compile(r"whey|protein|proteina|casein|caseina|creatin")
EXCLUDE = re.compile(r"\bbar\b|barra|wafer|covered|cookie|snack")
FLAVOR_OPTIONS = ("sabor",)
SIZE_OPTIONS = ("peso", "quantidade", "tamanho")


class GoldNutritionAdapter(StoreAdapter):
    slug = "gold-nutrition"
    name = "Gold Nutrition"
    website = BASE

    def __init__(self, http=None):
        super().__init__(http)
        self._products = None  # product URL -> Shopify product, loaded once per run

    def discover(self):
        return list(self._feed())

    def fetch(self, url, skip_nutrition_for=frozenset()):
        product = self._feed().get(url)
        return PageResult(items=parse_product(product, url)) if product else PageResult()

    def _feed(self):
        if self._products is None:
            self._products = {}
            for page in range(1, 20):
                response = self.http.get(FEED_URL, params={"limit": PAGE_SIZE, "page": page})
                response.raise_for_status()
                products = response.json().get("products", [])
                for product in products:
                    if is_tracked(product["title"]):
                        self._products[f"{BASE}/products/{product['handle']}"] = product
                if len(products) < PAGE_SIZE:
                    break
        return self._products


def is_tracked(title):
    title = plain(title)
    return bool(INCLUDE.search(title)) and not EXCLUDE.search(title)


def category_of(title):
    title = plain(title)
    return "Creatina" if "creatin" in title and not re.search(r"whey|protein", title) else "Proteína"


def option_value(product, variant, names):
    """The variant's value for the first product option whose name is in `names` ('' if none)."""
    for position, option in enumerate(product.get("options", []), 1):
        if plain(option.get("name")) in names:
            return variant.get(f"option{position}") or ""
    return ""


def parse_product(product, url):
    title = product["title"]
    images = product.get("images") or []
    items = []
    for variant in product.get("variants", []):
        price = to_decimal(variant.get("price"))
        if price is None:
            continue
        list_price = to_decimal(variant.get("compare_at_price"))
        # Size: a weight option, else the title, else Shopify's `grams` (the shipping weight,
        # which this store sets to the net weight in nearly every case).
        size = size_in_grams(option_value(product, variant, SIZE_OPTIONS)) or size_in_grams(title)
        if size is None and variant.get("grams"):
            size = to_decimal(variant["grams"])
        items.append(
            ScrapedItem(
                store_sku=str(variant["id"]),
                url=url,
                brand="Gold Nutrition",
                product_name=re.sub(r"\s*\d+\s*g$", "", title, flags=re.IGNORECASE),
                flavor=option_value(product, variant, FLAVOR_OPTIONS),
                size_g=size,
                price=price,
                list_price=list_price if list_price and list_price > price else None,
                in_stock=bool(variant.get("available")),
                category=category_of(title),
                image_url=images[0]["src"] if images else "",
            )
        )
    return items
