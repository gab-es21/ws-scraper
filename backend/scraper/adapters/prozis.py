"""
Prozis (prozis.com/pt/pt).

discover: the products sitemap, pre-filtered on URL slug.
fetch:    1. product page        -> groupId, name, image (JSON-LD)
          2. product/index       -> breadcrumbs (category), every flavor × size SKU with
                                    price, crossed-out price and stock, best-price coupons
          3. product/nutrition-table, once per flavor, only when not checked recently

Prozis' advertised price already includes its best public coupon (the JSON-LD
`price` equals the crossed-out price minus e.g. the 'SUPER' 15 % code), so that
price is stored as-is and the coupon only as information.
"""

import gzip
import re

from ..recording import ScrapedItem
from .base import PageResult, ScrapedCoupon, StoreAdapter, jsonld_objects, plain, size_in_grams, to_decimal

BASE = "https://www.prozis.com/pt/pt"
SITEMAP_URL = "https://prozis.com/pt/pt/sitemap_products.gz"
XHR_HEADERS = {"X-Requested-With": "XMLHttpRequest", "Accept": "application/json, */*"}

# Cheap pre-filter on the URL slug, to avoid fetching ~1900 pages a day.
# The breadcrumb category (TRACKED_CATEGORIES) is what finally decides.
SLUG_INCLUDE = re.compile(r"whey|protein|proteina|casein|caseina|isolate|isolada|creatin|creapure|micronpure")
SLUG_EXCLUDE = re.compile(
    r"bar|barra|cookie|puff|wafer|snack|cereal|crisp|pancake|panqueca|oat|aveia|bolacha|biscoit|brownie"
    r"|spread|gelado|drink|bebida|shaker|pasta|esparguete|pizza|muffin|pudding|pudim|bowl|chips|mug-cake"
    r"|leggings|saqueta|sachet"
)
TRACKED_CATEGORIES = ("proteina", "creatina")

SIZE_SUFFIX = re.compile(r"\s*\d+(?:[.,]\d+)?\s*(?:g|kg)\s*$", re.IGNORECASE)


class ProzisAdapter(StoreAdapter):
    slug = "prozis"
    name = "Prozis"
    website = BASE

    def __init__(self, http=None):
        super().__init__(http)
        # Each size of a product has its own URL and group, but every group's index lists the
        # SKUs of all sizes. Remember what this run already covered to fetch each SKU once.
        self._fetched_groups = set()
        self._sku_groups = {}

    def discover(self):
        response = self.http.get(SITEMAP_URL)
        response.raise_for_status()
        return parse_sitemap(response.content)

    def fetch(self, url, skip_nutrition_for=frozenset()):
        page = self.http.get(url)
        if page.status_code in (404, 410):
            return PageResult()
        page.raise_for_status()

        group_id = parse_group_id(page.text)
        if group_id in self._fetched_groups:
            return PageResult()
        self._fetched_groups.add(group_id)

        index = self.http.get(f"{BASE}/product/index", params={"_id": group_id}, headers=XHR_HEADERS)
        index.raise_for_status()
        data = index.json()

        new_skus = {}
        for sku in data.get("addToCart", {}).get("products", []):
            if sku.get("sku") and sku["sku"] not in self._sku_groups:
                new_skus[sku["sku"]] = sku.get("groupId") or group_id
        self._sku_groups.update(new_skus)
        self._fetched_groups.update(new_skus.values())

        category = tracked_category(data)
        if category is None:
            return PageResult()

        items = [item for item in parse_items(data, page.text, url, category) if item.store_sku in new_skus]
        self._add_nutrition(items, skip_nutrition_for)
        return PageResult(items=items, coupons=parse_coupons(data))

    def _add_nutrition(self, items, skip_nutrition_for):
        """Nutrition is per flavor: fetch it once per flavor that has a SKU needing it."""
        by_flavor = {}
        for item in items:
            by_flavor.setdefault(item.flavor, []).append(item)

        for flavor_items in by_flavor.values():
            if all(item.store_sku in skip_nutrition_for for item in flavor_items):
                continue
            first = flavor_items[0]
            response = self.http.get(
                f"{BASE}/product/nutrition-table",
                params={"_id": self._sku_groups[first.store_sku], "sku": first.store_sku},
                headers=XHR_HEADERS,
            )
            if response.status_code != 200 or not response.text.strip():
                continue
            for field, value in parse_nutrition(response.json()).items():
                for item in flavor_items:
                    setattr(item, field, value)


def parse_sitemap(content):
    if content[:2] == b"\x1f\x8b":
        content = gzip.decompress(content)
    urls = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", content.decode("utf-8", "replace"))
    return [url for url in urls if is_candidate(url)]


def is_candidate(url):
    slug = url.rstrip("/").rsplit("/", 1)[-1]
    return bool(SLUG_INCLUDE.search(slug)) and not SLUG_EXCLUDE.search(slug)


def parse_group_id(html):
    match = re.search(r'"groupId"\s*:\s*"(\d+)"', html)
    if not match:
        raise ValueError("no groupId on the product page")
    return match.group(1)


def tracked_category(index_data):
    """The product's own category (e.g. 'Proteína Whey') if it is a tracked one, else None."""
    links = index_data.get("breadcrumbs", {}).get("links", [])
    crumbs = [link.get("txt", "") for link in links[1:-1]]  # drop the 'Prozis' root and the product itself
    if not any(plain(crumb).startswith(TRACKED_CATEGORIES) for crumb in crumbs):
        return None
    return crumbs[-1]


def parse_items(index_data, page_html, url, category):
    product = (jsonld_objects(page_html, "Product") or [{}])[0]
    full_name = product.get("name", "")
    image = product.get("image", "")
    if isinstance(image, list):
        image = image[0] if image else ""
    if image.startswith("//"):
        image = "https:" + image

    items = []
    for sku in index_data.get("addToCart", {}).get("products", []):
        if not sku.get("isVisible", True):
            continue
        price = to_decimal(sku.get("price"))
        if price is None:
            continue
        list_price = to_decimal(sku.get("priceReference"))
        items.append(
            ScrapedItem(
                store_sku=sku["sku"],
                url=url,
                brand="Prozis",
                product_name=SIZE_SUFFIX.sub("", full_name) or full_name,
                flavor=sku.get("flavorDescription") or "",
                size_g=size_in_grams(sku.get("optionDescription")) or size_in_grams(full_name),
                price=price,
                list_price=list_price if list_price and list_price > price else None,
                in_stock=(sku.get("stock") or 0) > 0 and sku.get("status") == "AC",
                category=category,
                image_url=image,
            )
        )
    return items


def parse_nutrition(nutrition_data):
    """Grams per 100 g of protein, carbs and fat from the nutrition-table endpoint."""
    nutrients = nutrition_data.get("nutTable", {}).get("table", {}).get("nutrients", [])
    labels = {
        "protein_g": ("proteina",),
        "carbs_g": ("hidratos de carbono", "carboidratos"),
        "fat_g": ("lipidos", "gordura"),
    }
    values = {}
    for nutrient in nutrients:
        label = plain(nutrient.get("name"))
        for field, prefixes in labels.items():
            if field not in values and label.startswith(prefixes):
                values[field] = to_decimal((nutrient.get("amount") or {}).get("by100"))
    return values


def parse_coupons(index_data):
    # The coupon's own text names the product it was shown on; coupons are stored per store,
    # so keep a generic description.
    coupons = []
    for coupon in index_data.get("bestPriceCoupons") or []:
        discount = to_decimal(coupon.get("discount"))
        if coupon.get("coupon") and discount:
            coupons.append(
                ScrapedCoupon(
                    code=coupon["coupon"],
                    discount_percent=discount,
                    description=f"{discount:g}% off the crossed-out price (already included in Prozis' price)",
                )
            )
    return coupons
