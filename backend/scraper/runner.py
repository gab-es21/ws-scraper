"""Run one store adapter end to end and record the results (see recording.py)."""

from dataclasses import dataclass, field
from datetime import timedelta

from django.utils import timezone

from .adapters.base import Blocked
from .models import Coupon, Listing, ScrapeRun, Store
from .recording import record_item

# Nutrition rarely changes; re-check each listing at most this often.
NUTRITION_MAX_AGE = timedelta(days=7)
# Stop the run when this many product pages in a row fail (site down, blocked, layout changed).
MAX_CONSECUTIVE_ERRORS = 5


@dataclass
class Progress:
    run: ScrapeRun
    log: callable
    lines: list = field(default_factory=list)
    seen_skus: set = field(default_factory=set)
    seen_coupons: set = field(default_factory=set)
    failed_urls: set = field(default_factory=set)

    def note(self, message):
        self.lines.append(message)
        self.log(message)


def run_store(adapter, urls=None, limit=None, log=print):
    """
    Scrape one store with `adapter`.

    `urls` replaces discovery (e.g. to re-check a single product); `limit` caps the number of
    product pages. Listings and coupons that disappeared are only deactivated on full runs.
    """
    store, _ = Store.objects.get_or_create(
        slug=adapter.slug, defaults={"name": adapter.name, "website": adapter.website}
    )
    run = ScrapeRun.objects.create(store=store)
    progress = Progress(run=run, log=log)
    try:
        targets = list(urls) if urls else adapter.discover()
        targets = targets[:limit] if limit else targets
        progress.note(f"{store.name}: {len(targets)} product pages")
        scrape_pages(adapter, store, targets, progress)
        if not urls and not limit:
            gone = deactivate_missing(store, progress)
            progress.note(f"{gone} listings no longer on the store")
        run.status = ScrapeRun.Status.PARTIAL if run.errors else ScrapeRun.Status.SUCCESS
    except Exception as error:
        progress.note(f"STOPPED: {error}")
        run.status = ScrapeRun.Status.FAILED
    finally:
        run.finished_at = timezone.now()
        run.log = "\n".join(progress.lines)[-20000:]
        run.save()

    progress.note(
        f"{store.name}: {run.status} — {run.items_found} variants, {run.prices_changed} price changes, "
        f"{run.nutrition_changed} nutrition changes, {run.errors} errors"
    )
    return run


def scrape_pages(adapter, store, targets, progress):
    run = progress.run
    fresh_nutrition = recently_checked_nutrition(store)
    consecutive_errors = 0

    for position, url in enumerate(targets, 1):
        try:
            result = adapter.fetch(url, skip_nutrition_for=fresh_nutrition)
        except Blocked:
            raise
        except Exception as error:
            progress.failed_urls.add(url)
            run.errors += 1
            consecutive_errors += 1
            progress.note(f"[{position}/{len(targets)}] ERROR {url}: {error}")
            if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                raise Blocked(f"{consecutive_errors} product pages in a row failed")
            continue

        consecutive_errors = 0
        for item in result.items:
            recorded = record_item(store, item, seen_at=timezone.now())
            progress.seen_skus.add(item.store_sku)
            run.items_found += 1
            run.prices_changed += recorded.price_changed
            run.nutrition_changed += recorded.nutrition_changed
        for coupon in result.coupons:
            save_coupon(store, coupon)
            progress.seen_coupons.add(coupon.code)
        if result.items:
            progress.note(f"[{position}/{len(targets)}] {len(result.items)} variants  {url}")


def recently_checked_nutrition(store):
    since = timezone.now() - NUTRITION_MAX_AGE
    return frozenset(
        Listing.objects.filter(
            store=store, nutrition_records__valid_to__isnull=True, nutrition_records__last_checked_at__gte=since
        ).values_list("store_sku", flat=True)
    )


def save_coupon(store, coupon):
    Coupon.objects.update_or_create(
        store=store,
        code=coupon.code,
        defaults={
            "discount_percent": coupon.discount_percent,
            "description": coupon.description[:300],
            "is_active": True,
            "last_seen_at": timezone.now(),
        },
    )


def deactivate_missing(store, progress):
    """Mark listings and coupons not seen in a full run as inactive (pages that errored don't count)."""
    gone = (
        Listing.objects.filter(store=store, is_active=True)
        .exclude(store_sku__in=progress.seen_skus)
        .exclude(url__in=progress.failed_urls)
        .update(is_active=False)
    )
    Coupon.objects.filter(store=store, is_active=True).exclude(code__in=progress.seen_coupons).update(is_active=False)
    return gone
