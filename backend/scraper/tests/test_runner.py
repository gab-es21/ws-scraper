from decimal import Decimal

import pytest

from scraper.adapters.base import Blocked, PageResult, ScrapedCoupon, StoreAdapter
from scraper.models import Coupon, Listing, ScrapeRun
from scraper.recording import ScrapedItem
from scraper.runner import MAX_CONSECUTIVE_ERRORS, run_store


def scraped(sku, price="10.00", protein="80"):
    return ScrapedItem(
        store_sku=sku,
        url=f"https://fake.example/{sku}",
        brand="Fake",
        product_name=f"Product {sku}",
        size_g=Decimal("1000"),
        price=Decimal(price),
        in_stock=True,
        protein_g=Decimal(protein) if protein else None,
    )


def page(*skus, coupons=()):
    return PageResult(items=[scraped(s) for s in skus], coupons=list(coupons))


class FakeAdapter(StoreAdapter):
    slug = "fake"
    name = "Fake Store"
    website = "https://fake.example"

    def __init__(self, pages):
        self.pages = pages  # url -> PageResult, or an exception to raise
        self.nutrition_skips = []

    def discover(self):
        return list(self.pages)

    def fetch(self, url, skip_nutrition_for=frozenset()):
        self.nutrition_skips.append(skip_nutrition_for)
        outcome = self.pages[url]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def run(pages, **kwargs):
    return run_store(FakeAdapter(pages), log=lambda message: None, **kwargs)


@pytest.fixture(autouse=True)
def _db(db):
    pass


def test_full_run_records_items_coupons_and_counters():
    coupon = ScrapedCoupon(code="SUPER", discount_percent=Decimal("15"))
    result = run({"https://fake.example/p1": page("A", "B", coupons=[coupon]), "https://fake.example/p2": page()})

    assert result.status == ScrapeRun.Status.SUCCESS
    assert (result.items_found, result.prices_changed, result.nutrition_changed, result.errors) == (2, 2, 2, 0)
    assert result.store.slug == "fake"
    assert Listing.objects.filter(is_active=True).count() == 2
    assert Coupon.objects.get().code == "SUPER"
    assert result.finished_at is not None


def test_unchanged_second_run_records_no_changes():
    pages = {"https://fake.example/p1": page("A", "B")}
    run(pages)

    second = run(pages)

    assert (second.items_found, second.prices_changed, second.nutrition_changed) == (2, 0, 0)


def test_full_run_deactivates_listings_and_coupons_that_disappeared():
    coupon = ScrapedCoupon(code="SUPER", discount_percent=Decimal("15"))
    run({"https://fake.example/p1": page("A", "B", coupons=[coupon])})

    run({"https://fake.example/p1": page("A")})

    assert set(Listing.objects.filter(is_active=True).values_list("store_sku", flat=True)) == {"A"}
    assert not Coupon.objects.get().is_active


def test_pages_that_failed_do_not_deactivate_their_listings():
    run({"https://fake.example/A": page("A"), "https://fake.example/B": page("B")})

    result = run({"https://fake.example/A": page("A"), "https://fake.example/B": RuntimeError("timeout")})

    assert result.status == ScrapeRun.Status.PARTIAL
    assert result.errors == 1
    assert Listing.objects.filter(is_active=True).count() == 2


@pytest.mark.parametrize("kwargs", [{"limit": 1}, {"urls": ["https://fake.example/p1"]}])
def test_partial_runs_never_deactivate(kwargs):
    run({"https://fake.example/p1": page("A"), "https://fake.example/p2": page("B")})

    run({"https://fake.example/p1": page("A"), "https://fake.example/p2": page()}, **kwargs)

    assert Listing.objects.filter(is_active=True).count() == 2


def test_blocked_store_stops_the_run_but_keeps_what_was_recorded():
    result = run({"https://fake.example/p1": page("A"), "https://fake.example/p2": Blocked("429")})

    assert result.status == ScrapeRun.Status.FAILED
    assert result.items_found == 1
    assert "STOPPED" in result.log


def test_too_many_consecutive_errors_stop_the_run():
    pages = {f"https://fake.example/p{i}": RuntimeError("layout changed") for i in range(MAX_CONSECUTIVE_ERRORS + 3)}

    result = run(pages)

    assert result.status == ScrapeRun.Status.FAILED
    assert result.errors == MAX_CONSECUTIVE_ERRORS


def test_listings_with_recent_nutrition_are_passed_as_skippable():
    pages = {"https://fake.example/p1": page("A")}
    run(pages)
    adapter = FakeAdapter(pages)

    run_store(adapter, log=lambda message: None)

    assert adapter.nutrition_skips == [frozenset({"A"})]
