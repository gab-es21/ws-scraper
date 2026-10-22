"""
Zumub (zumub.com/PT).

discover: the protein and creatine category pages; each lists its products as JSON-LD
          (CollectionPage → ItemList) and paginates with ?page=N. Zumub publishes no sitemap.
fetch:    the product page: JSON-LD ProductGroup with one variant per size (flavors share the
          size's SKU) with price, list price, stock and EAN, from several brands. Nutrition comes
          from the page's table, usually per serving ("Por 30 g") and scaled to 100 g.
"""

from .base import PageResult, StoreAdapter, jsonld_objects, nutrition_from_tables
from .jsonld import product_group, scraped_items

BASE = "https://www.zumub.com/PT"
CATEGORY_PAGES = [
    f"{BASE}/proteinas/whey",
    f"{BASE}/proteinas/caseina",
    f"{BASE}/proteinas/proteina-vegetal",
    f"{BASE}/proteinas/ovo",
    f"{BASE}/creatina",
]
MAX_PAGES = 30


class ZumubAdapter(StoreAdapter):
    slug = "zumub"
    name = "Zumub"
    website = BASE

    def discover(self):
        urls, seen = [], set()
        for category in CATEGORY_PAGES:
            for page in range(1, MAX_PAGES + 1):
                response = self.http.get(category, params={"page": page} if page > 1 else None)
                if response.status_code == 404:
                    break
                response.raise_for_status()
                new = [
                    u
                    for u in dict.fromkeys(listed_products(response.content.decode("utf-8", "replace")))
                    if u not in seen
                ]
                if not new:  # past the last page, Zumub repeats the last page or lists nothing
                    break
                urls += new
                seen.update(new)
        return urls

    def fetch(self, url, skip_nutrition_for=frozenset()):
        page = self.http.get(url)
        if page.status_code in (404, 410):
            return PageResult()
        page.raise_for_status()
        return PageResult(items=parse_product_page(page.content.decode("utf-8", "replace"), url))


def listed_products(html):
    urls = []
    for collection in jsonld_objects(html, "CollectionPage"):
        for element in (collection.get("mainEntity") or {}).get("itemListElement", []):
            if element.get("url"):
                urls.append(element["url"])
    return urls


def parse_product_page(html, url):
    group, variants = product_group(html)
    if group is None:
        return []
    return scraped_items(group, variants, url, default_brand="Zumub", nutrition=nutrition_from_tables(html))
