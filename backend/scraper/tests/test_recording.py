from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from django.db import IntegrityError, transaction

from scraper.models import (
    Listing,
    NutritionRecord,
    PriceRecord,
    Product,
    Store,
    Variant,
    price_per_100g,
    price_per_100g_protein,
)
from scraper.recording import ScrapedItem, record_item

T0 = datetime(2026, 10, 1, 6, 0, tzinfo=timezone.utc)


def day(n):
    return T0 + timedelta(days=n)


def item(**overrides):
    values = {
        "store_sku": "NUT00/1756750163",
        "url": "https://www.prozis.com/pt/pt/prozis/whey-fibre-700-g",
        "brand": "Prozis",
        "product_name": "Whey + Fibre",
        "flavor": "Chocolate e Avelã",
        "size_g": Decimal("700"),
        "price": Decimal("19.54"),
        "list_price": Decimal("22.99"),
        "in_stock": True,
        "protein_g": Decimal("43"),
        "carbs_g": Decimal("40"),
        "fat_g": Decimal("2.9"),
    }
    values.update(overrides)
    return ScrapedItem(**values)


@pytest.fixture
def store(db):
    return Store.objects.create(slug="prozis", name="Prozis")


def test_first_scrape_creates_catalog_and_current_records(store):
    result = record_item(store, item(), seen_at=day(0))

    assert result.price_changed and result.nutrition_changed
    variant = result.listing.variant
    assert (variant.product.brand.name, variant.product.name) == ("Prozis", "Whey + Fibre")
    assert (variant.flavor, variant.size_g) == ("Chocolate e Avelã", Decimal("700.0"))

    price = result.listing.current_price()
    assert (price.price, price.list_price, price.in_stock) == (Decimal("19.54"), Decimal("22.99"), True)
    assert (price.valid_from, price.valid_to, price.last_checked_at) == (day(0), None, day(0))

    nutrition = result.listing.current_nutrition()
    assert (nutrition.protein_g, nutrition.carbs_g, nutrition.fat_g) == (Decimal("43"), Decimal("40"), Decimal("2.9"))


def test_unchanged_values_only_move_last_checked_at(store):
    record_item(store, item(), seen_at=day(0))
    result = record_item(store, item(), seen_at=day(1))

    assert not result.price_changed and not result.nutrition_changed
    price = PriceRecord.objects.get()
    assert (price.valid_from, price.valid_to, price.last_checked_at) == (day(0), None, day(1))
    assert NutritionRecord.objects.get().last_checked_at == day(1)


def test_price_change_closes_current_record_and_opens_a_new_one(store):
    record_item(store, item(), seen_at=day(0))
    record_item(store, item(), seen_at=day(1))
    result = record_item(store, item(price=Decimal("17.99")), seen_at=day(2))

    assert result.price_changed and not result.nutrition_changed
    old, new = PriceRecord.objects.order_by("valid_from")
    assert (old.price, old.valid_from, old.valid_to, old.last_checked_at) == (Decimal("19.54"), day(0), day(2), day(1))
    assert (new.price, new.valid_from, new.valid_to) == (Decimal("17.99"), day(2), None)


@pytest.mark.parametrize(
    "change",
    [{"list_price": None}, {"in_stock": False}],
    ids=["sale ends", "out of stock"],
)
def test_list_price_and_stock_changes_are_recorded(store, change):
    record_item(store, item(), seen_at=day(0))
    assert record_item(store, item(**change), seen_at=day(1)).price_changed
    assert PriceRecord.objects.count() == 2


def test_price_going_back_to_an_old_value_is_a_new_period(store):
    for n, price in enumerate(["19.54", "17.99", "19.54"]):
        record_item(store, item(price=Decimal(price)), seen_at=day(n))

    prices = list(PriceRecord.objects.order_by("valid_from").values_list("price", "valid_from", "valid_to"))
    assert prices == [
        (Decimal("19.54"), day(0), day(1)),
        (Decimal("17.99"), day(1), day(2)),
        (Decimal("19.54"), day(2), None),
    ]


def test_equivalent_number_formats_are_not_changes(store):
    record_item(store, item(price=19.54, protein_g=43.0), seen_at=day(0))
    result = record_item(store, item(price="19.540", protein_g="43"), seen_at=day(1))

    assert not result.price_changed and not result.nutrition_changed


def test_missing_nutrition_keeps_what_we_already_know(store):
    record_item(store, item(), seen_at=day(0))
    result = record_item(store, item(protein_g=None, carbs_g=None, fat_g=None), seen_at=day(1))

    assert not result.nutrition_changed
    nutrition = NutritionRecord.objects.get()
    assert (nutrition.protein_g, nutrition.valid_to, nutrition.last_checked_at) == (Decimal("43"), None, day(0))


def test_nutrition_change_is_recorded(store):
    record_item(store, item(), seen_at=day(0))
    result = record_item(store, item(protein_g=Decimal("44.5")), seen_at=day(5))

    assert result.nutrition_changed and not result.price_changed
    assert list(NutritionRecord.objects.order_by("valid_from").values_list("protein_g", "valid_to")) == [
        (Decimal("43"), day(5)),
        (Decimal("44.5"), None),
    ]


def test_same_sku_updates_the_listing_instead_of_duplicating_it(store):
    record_item(store, item(), seen_at=day(0))
    record_item(store, item(url="https://www.prozis.com/pt/pt/prozis/new-slug"), seen_at=day(1))

    listing = Listing.objects.get()
    assert listing.url == "https://www.prozis.com/pt/pt/prozis/new-slug"
    assert (listing.first_seen_at, listing.last_seen_at) == (day(0), day(1))


def test_flavors_and_sizes_are_variants_of_one_product(store):
    record_item(store, item(), seen_at=day(0))
    record_item(store, item(store_sku="NUT00/1756750089", flavor="Baunilha"), seen_at=day(0))
    record_item(store, item(store_sku="NUT00/1756751163", size_g=Decimal("2000")), seen_at=day(0))

    assert Product.objects.count() == 1
    assert Variant.objects.count() == 3
    assert Listing.objects.count() == 3


def test_a_listing_cannot_have_two_current_prices(store):
    listing = record_item(store, item(), seen_at=day(0)).listing

    with pytest.raises(IntegrityError), transaction.atomic():
        PriceRecord.objects.create(
            listing=listing, price=Decimal("1"), in_stock=True, valid_from=day(1), last_checked_at=day(1)
        )


def test_price_per_100g_helpers():
    assert price_per_100g(Decimal("19.54"), Decimal("700")) == Decimal("2.79")
    assert price_per_100g_protein(Decimal("19.54"), Decimal("700"), Decimal("43")) == Decimal("6.49")
    assert price_per_100g(Decimal("19.54"), None) is None
    assert price_per_100g_protein(Decimal("19.54"), Decimal("700"), None) is None
