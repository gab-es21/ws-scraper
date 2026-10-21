"""
Data model.

    Store ─┐
    Brand ─┴─► Product ─► Variant (flavor, size)
                             │
                             └─► Listing (store, store_sku, url)
                                    ├─► PriceRecord      price, list price, stock
                                    └─► NutritionRecord  protein / carbs / fat per 100 g

PriceRecord and NutritionRecord only get a new row when a value changes.
Each row is valid from `valid_from` until `valid_to`; the current row has
`valid_to = NULL`. `last_checked_at` is bumped on every scrape that finds the
same values, so the history shows exactly when each change happened.
"""

from decimal import Decimal

from django.db import models
from django.db.models import Q
from django.utils import timezone


class Store(models.Model):
    slug = models.SlugField(unique=True, help_text="Matches the scraper adapter name, e.g. 'prozis'.")
    name = models.CharField(max_length=100)
    website = models.URLField(blank=True)

    def __str__(self):
        return self.name


class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name="products")
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=50, blank=True)
    image_url = models.URLField(max_length=500, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["brand", "name"], name="unique_product_per_brand")]

    def __str__(self):
        return f"{self.brand} {self.name}"


class Variant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    flavor = models.CharField(max_length=100, blank=True)
    size_g = models.DecimalField(max_digits=8, decimal_places=1, null=True, blank=True)
    gtin = models.CharField(max_length=14, blank=True, db_index=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["product", "flavor", "size_g"], name="unique_variant_per_product")
        ]

    def __str__(self):
        parts = [str(self.product), self.flavor, f"{self.size_g:g} g" if self.size_g else ""]
        return " · ".join(p for p in parts if p)


class Listing(models.Model):
    """A variant as sold by one store."""

    store = models.ForeignKey(Store, on_delete=models.PROTECT, related_name="listings")
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE, related_name="listings")
    store_sku = models.CharField(max_length=100)
    url = models.URLField(max_length=500)
    is_active = models.BooleanField(default=True)
    first_seen_at = models.DateTimeField(default=timezone.now)
    last_seen_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["store", "store_sku"], name="unique_sku_per_store")]

    def __str__(self):
        return f"{self.variant} @ {self.store}"

    def current_price(self):
        return self.price_records.filter(valid_to__isnull=True).first()

    def current_nutrition(self):
        return self.nutrition_records.filter(valid_to__isnull=True).first()


class ChangeRecord(models.Model):
    """Common fields for value histories that only store changes."""

    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField(null=True, blank=True)
    last_checked_at = models.DateTimeField()

    class Meta:
        abstract = True
        ordering = ["-valid_from"]


class PriceRecord(ChangeRecord):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="price_records")
    price = models.DecimalField(max_digits=8, decimal_places=2, help_text="What the customer pays now.")
    list_price = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True, help_text="Crossed-out price, when on sale."
    )
    in_stock = models.BooleanField()

    class Meta(ChangeRecord.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["listing"], condition=Q(valid_to__isnull=True), name="one_current_price_per_listing"
            )
        ]

    def __str__(self):
        return f"{self.listing}: {self.price} € from {self.valid_from:%Y-%m-%d}"


class NutritionRecord(ChangeRecord):
    """Grams per 100 g of product."""

    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="nutrition_records")
    protein_g = models.DecimalField(max_digits=5, decimal_places=2)
    carbs_g = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    fat_g = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta(ChangeRecord.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["listing"], condition=Q(valid_to__isnull=True), name="one_current_nutrition_per_listing"
            )
        ]

    def __str__(self):
        return f"{self.listing}: {self.protein_g} g protein/100 g"


class Coupon(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="coupons")
    code = models.CharField(max_length=50)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2)
    description = models.CharField(max_length=300, blank=True)
    is_active = models.BooleanField(default=True)
    first_seen_at = models.DateTimeField(default=timezone.now)
    last_seen_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["store", "code"], name="unique_coupon_per_store")]

    def __str__(self):
        return f"{self.code} (-{self.discount_percent:g}%) @ {self.store}"


class ScrapeRun(models.Model):
    class Status(models.TextChoices):
        RUNNING = "running"
        SUCCESS = "success"
        PARTIAL = "partial", "Finished with errors"
        FAILED = "failed"

    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="runs")
    started_at = models.DateTimeField(default=timezone.now)
    finished_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.RUNNING)
    items_found = models.PositiveIntegerField(default=0)
    prices_changed = models.PositiveIntegerField(default=0)
    nutrition_changed = models.PositiveIntegerField(default=0)
    errors = models.PositiveIntegerField(default=0)
    log = models.TextField(blank=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.store} {self.started_at:%Y-%m-%d %H:%M} ({self.status})"


def price_per_100g(price, size_g):
    if price is None or not size_g:
        return None
    return (Decimal(price) * 100 / Decimal(size_g)).quantize(Decimal("0.01"))


def price_per_100g_protein(price, size_g, protein_g):
    per_100g = price_per_100g(price, size_g)
    if per_100g is None or not protein_g:
        return None
    return (per_100g * 100 / Decimal(protein_g)).quantize(Decimal("0.01"))
