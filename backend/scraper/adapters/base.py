"""Shared pieces for store adapters: a polite HTTP client and the adapter interface."""

import gzip
import json
import random
import re
import time
import unicodedata
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from html import unescape

import requests
from bs4 import BeautifulSoup

from ..recording import ScrapedItem

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


class Blocked(Exception):
    """The store keeps refusing requests (429/403/503); the run should stop."""


class HttpClient:
    """requests.Session with a random pause between requests and back-off on 429/503."""

    def __init__(self, delay=(1.0, 2.5), timeout=20, retries=2, backoff=30, sleep=time.sleep):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "pt-PT,pt;q=0.9,en;q=0.8"})
        self.delay = delay
        self.timeout = timeout
        self.retries = retries
        self.backoff = backoff
        self.sleep = sleep
        self._last_request = 0.0

    def get(self, url, **kwargs):
        for attempt in range(self.retries + 1):
            wait = self._last_request + random.uniform(*self.delay) - time.monotonic()
            if wait > 0:
                self.sleep(wait)
            response = self.session.get(url, timeout=self.timeout, **kwargs)
            self._last_request = time.monotonic()
            if response.status_code not in (429, 503):
                return response
            retry_after = response.headers.get("Retry-After", "")
            self.sleep(int(retry_after) if retry_after.isdigit() else self.backoff * (attempt + 1))
        raise Blocked(f"{url} answered {response.status_code} {self.retries + 1} times")


@dataclass
class ScrapedCoupon:
    code: str
    discount_percent: Decimal
    description: str = ""


@dataclass
class PageResult:
    """What one product URL yielded. `items` is empty for products outside the tracked categories."""

    items: list[ScrapedItem] = field(default_factory=list)
    coupons: list[ScrapedCoupon] = field(default_factory=list)


class StoreAdapter:
    slug: str
    name: str
    website: str

    def __init__(self, http=None):
        self.http = http or HttpClient()

    def discover(self):
        """Return the product page URLs to scrape."""
        raise NotImplementedError

    def fetch(self, url, skip_nutrition_for=frozenset()):
        """
        Return a PageResult for one product page.

        `skip_nutrition_for` holds store SKUs whose nutrition was checked recently;
        adapters may leave their nutrition empty to save requests.
        """
        raise NotImplementedError


def to_decimal(text):
    """'€19.54' -> 19.54, '2,90 g' -> 2.90, '<0.5 g' -> 0.5; None when there is no number."""
    match = re.search(r"\d+(?:[.,]\d+)?", str(text or ""))
    if not match:
        return None
    try:
        return Decimal(match.group().replace(",", "."))
    except InvalidOperation:
        return None


def size_in_grams(text):
    """'700 g' -> 700, '2.27 kg' -> 2270; None for '90 cápsulas', '20 doses', ..."""
    match = re.search(r"(\d+(?:[.,]\d+)?)\s*(kg|g)\b", str(text or ""), re.IGNORECASE)
    if not match:
        return None
    value = Decimal(match.group(1).replace(",", "."))
    return value * 1000 if match.group(2).lower() == "kg" else value


def plain(text):
    """Lowercase without accents, for matching labels like 'Lípidos' or 'Proteína'."""
    decomposed = unicodedata.normalize("NFKD", str(text or ""))
    return "".join(c for c in decomposed if not unicodedata.combining(c)).lower().strip()


# Row labels of nutrition tables (accent-free, lowercase prefixes; stores mix Portuguese and English).
# Prefix matching skips sub-rows such as "dos quais saturados" / "of which sugars".
NUTRIENT_LABELS = {
    "protein_g": ("proteina", "protein"),
    "carbs_g": ("hidratos de carbono", "carboidratos", "carbohidratos", "carbohydrate"),
    "fat_g": ("lipidos", "gordura", "fat"),
}


def nutrient_field(label):
    """'Lípidos' -> 'fat_g', 'Proteínas' -> 'protein_g'; None for other rows."""
    label = plain(label)
    for name, prefixes in NUTRIENT_LABELS.items():
        if label.startswith(prefixes):
            return name
    return None


def nutrition_from_tables(html):
    """
    Protein, carbs and fat per 100 g from the first HTML table that has them.

    Uses the "per 100 g" column; when the table only has a per-serving column
    ("Por 30 g"), scales it to 100 g.
    """
    for table in BeautifulSoup(html, "html.parser").find_all("table"):
        rows = [[c.get_text(" ", strip=True) for c in tr.find_all(["th", "td"])] for tr in table.find_all("tr")]
        column = _amount_column(rows)
        if column is None:
            continue
        offset_from_end, grams = column
        values = {}
        for row in rows:
            name = nutrient_field(row[0]) if row else None
            if name and name not in values and len(row) >= offset_from_end + 1:
                amount = to_decimal(row[len(row) - offset_from_end])
                if amount is not None:
                    values[name] = (amount * 100 / grams).quantize(Decimal("0.01"))
        if "protein_g" in values:
            return values
    return {}


def _amount_column(rows):
    """
    (position counted from the row end, grams the column refers to) of the best amount column:
    'Por 100 g' if present, else the first 'Por <n> g'. Counted from the end because header rows
    often lack the empty label cell that data rows have.
    """
    for row in rows:
        per_grams = [
            (i, Decimal(m.group(1).replace(",", ".")))
            for i, cell in enumerate(row)
            if (m := re.search(r"por\s*(\d+(?:[.,]\d+)?)\s*g\b", plain(cell)))
        ]
        if per_grams:
            index, grams = next(((i, g) for i, g in per_grams if g == 100), per_grams[0])
            return len(row) - index, grams
    return None


def sitemap_urls(content):
    """The <loc> URLs of a sitemap or sitemap index, gzipped or not."""
    if content[:2] == b"\x1f\x8b":
        content = gzip.decompress(content)
    return [unescape(url) for url in re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", content.decode("utf-8", "replace"))]


def jsonld_objects(html, type_name):
    """All schema.org JSON-LD objects of `type_name` on the page (top level, lists and @graph)."""
    found = []
    for script in BeautifulSoup(html, "html.parser").find_all("script", type="application/ld+json"):
        raw = re.sub(r"/\*<!\[CDATA\[\*/|/\*\]\]>\*/", "", script.get_text()).strip()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        candidates = data if isinstance(data, list) else data.get("@graph", [data])
        found += [c for c in candidates if isinstance(c, dict) and c.get("@type") == type_name]
    return found
