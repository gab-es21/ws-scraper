"""
Persist scraped data, storing a new price/nutrition row only when a value changes.

Adapters produce `ScrapedItem`s; `record_item` turns each one into
Brand → Product → Variant → Listing rows and updates the change histories.
"""

from dataclasses import dataclass
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from .models import Brand, Listing, NutritionRecord, PriceRecord, Product, Variant

CENT = Decimal("0.01")


@dataclass
class ScrapedItem:
    """One purchasable variant (flavor × size) as seen on a store."""

    store_sku: str
    url: str
    brand: str
    product_name: str
    price: Decimal
    in_stock: bool
    flavor: str = ""
    size_g: Decimal | None = None
    list_price: Decimal | None = None
    category: str = ""
    image_url: str = ""
    gtin: str = ""
    # grams per 100 g of product
    protein_g: Decimal | None = None
    carbs_g: Decimal | None = None
    fat_g: Decimal | None = None


@dataclass
class RecordResult:
    listing: Listing
    price_changed: bool
    nutrition_changed: bool


def _dec(value, places=CENT):
    if value is None:
        return None
    return Decimal(str(value)).quantize(places)


def _record_change(model, listing, values, seen_at):
    """
    Keep `values` as the current record of `model` for `listing`.

    Same values as the current record: only `last_checked_at` moves.
    Different values (or no record yet): close the current record at `seen_at`
    and open a new one. Returns True when a new record was created.
    """
    current = model.objects.filter(listing=listing, valid_to__isnull=True).first()
    if current and all(getattr(current, field) == value for field, value in values.items()):
        current.last_checked_at = seen_at
        current.save(update_fields=["last_checked_at"])
        return False

    if current:
        current.valid_to = seen_at
        current.save(update_fields=["valid_to"])
    model.objects.create(listing=listing, valid_from=seen_at, last_checked_at=seen_at, **values)
    return True


@transaction.atomic
def record_item(store, item, seen_at=None):
    seen_at = seen_at or timezone.now()

    brand, _ = Brand.objects.get_or_create(name=item.brand)
    product, _ = Product.objects.get_or_create(brand=brand, name=item.product_name)
    changed_fields = [
        f for f in ("category", "image_url") if getattr(item, f) and getattr(product, f) != getattr(item, f)
    ]
    for field in changed_fields:
        setattr(product, field, getattr(item, field))
    if changed_fields:
        product.save(update_fields=changed_fields)

    variant, _ = Variant.objects.get_or_create(
        product=product, flavor=item.flavor, size_g=_dec(item.size_g, Decimal("0.1"))
    )
    if item.gtin and variant.gtin != item.gtin:
        variant.gtin = item.gtin
        variant.save(update_fields=["gtin"])

    previous_variant_id = (
        Listing.objects.filter(store=store, store_sku=item.store_sku).values_list("variant_id", flat=True).first()
    )
    listing, _ = Listing.objects.update_or_create(
        store=store,
        store_sku=item.store_sku,
        defaults={"variant": variant, "url": item.url, "is_active": True, "last_seen_at": seen_at},
        create_defaults={
            "variant": variant,
            "url": item.url,
            "is_active": True,
            "first_seen_at": seen_at,
            "last_seen_at": seen_at,
        },
    )
    # The SKU now describes another variant (e.g. its size became known): the listing and its
    # history moved; drop the old variant if nothing else uses it.
    if previous_variant_id and previous_variant_id != variant.id:
        Variant.objects.filter(id=previous_variant_id, listings__isnull=True).delete()

    price_changed = _record_change(
        PriceRecord,
        listing,
        {"price": _dec(item.price), "list_price": _dec(item.list_price), "in_stock": item.in_stock},
        seen_at,
    )

    # No nutrition scraped this time: keep whatever we already know.
    nutrition_changed = False
    if item.protein_g is not None:
        nutrition_changed = _record_change(
            NutritionRecord,
            listing,
            {"protein_g": _dec(item.protein_g), "carbs_g": _dec(item.carbs_g), "fat_g": _dec(item.fat_g)},
            seen_at,
        )

    return RecordResult(listing=listing, price_changed=price_changed, nutrition_changed=nutrition_changed)
