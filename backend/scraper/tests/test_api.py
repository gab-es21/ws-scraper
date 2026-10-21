from datetime import datetime, timezone
from decimal import Decimal

import pytest

from scraper.models import Brand, Product, Store
from scraper.recording import ScrapedItem, record_item

T0 = datetime(2026, 10, 1, 6, 0, tzinfo=timezone.utc)


@pytest.fixture
def store(db):
    return Store.objects.create(slug="prozis", name="Prozis")


def scraped(**overrides):
    values = {
        "store_sku": "NUT00/1756750163",
        "url": "https://www.prozis.com/pt/pt/prozis/whey-fibre-700-g",
        "brand": "Prozis",
        "product_name": "Whey + Fibre",
        "size_g": Decimal("700"),
        "price": Decimal("19.54"),
        "in_stock": True,
        "protein_g": Decimal("43"),
    }
    values.update(overrides)
    return ScrapedItem(**values)


def test_extraction_status_shows_current_values(client, store):
    record_item(store, scraped(), seen_at=T0)
    record_item(store, scraped(price=Decimal("17.99")), seen_at=T0.replace(day=2))

    response = client.get("/api/extraction-status/")

    assert response.status_code == 200
    [row] = response.json()
    assert row["store"] == "Prozis"
    assert row["price_eur"] == 17.99
    assert row["price_per_100g"] == 2.57
    assert row["protein_g"] == 43.0
    assert row["is_available"] is True


def test_extraction_status_without_size_has_no_price_per_100g(client, store):
    record_item(store, scraped(size_g=None), seen_at=T0)

    [row] = client.get("/api/extraction-status/").json()

    assert row["weight_g"] is None
    assert row["price_per_100g"] is None


def test_products_can_be_filtered_by_brand(client, db):
    prozis, other = Brand.objects.create(name="Prozis"), Brand.objects.create(name="Other")
    Product.objects.create(brand=prozis, name="Whey + Fibre")
    Product.objects.create(brand=other, name="Iso Whey")

    names = [p["name"] for p in client.get(f"/api/products/?brand={prozis.id}").json()]

    assert names == ["Whey + Fibre"]


@pytest.mark.parametrize("url", ["/api/brands/", "/api/products/", "/api/stores/"])
def test_catalog_endpoints_are_read_only(client, db, url):
    assert client.post(url, {"name": "x"}).status_code == 405
