from django.contrib import admin

from .models import Brand, Coupon, Listing, NutritionRecord, PriceRecord, Product, ScrapeRun, Store, Variant


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "website")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    search_fields = ("name",)


class VariantInline(admin.TabularInline):
    model = Variant
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "brand", "category")
    list_filter = ("brand", "category")
    search_fields = ("name", "brand__name")
    inlines = [VariantInline]


@admin.register(Variant)
class VariantAdmin(admin.ModelAdmin):
    list_display = ("product", "flavor", "size_g", "gtin")
    search_fields = ("product__name", "flavor", "gtin")
    list_select_related = ("product__brand",)


class PriceRecordInline(admin.TabularInline):
    model = PriceRecord
    extra = 0
    fields = ("price", "list_price", "in_stock", "valid_from", "valid_to", "last_checked_at")
    readonly_fields = fields
    can_delete = False


class NutritionRecordInline(admin.TabularInline):
    model = NutritionRecord
    extra = 0
    fields = ("protein_g", "carbs_g", "fat_g", "valid_from", "valid_to", "last_checked_at")
    readonly_fields = fields
    can_delete = False


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ("variant", "store", "store_sku", "is_active", "last_seen_at")
    list_filter = ("store", "is_active")
    search_fields = ("store_sku", "variant__product__name")
    list_select_related = ("store", "variant__product__brand")
    inlines = [PriceRecordInline, NutritionRecordInline]


@admin.register(PriceRecord)
class PriceRecordAdmin(admin.ModelAdmin):
    list_display = ("listing", "price", "list_price", "in_stock", "valid_from", "valid_to", "last_checked_at")
    list_filter = ("listing__store", "in_stock")
    list_select_related = ("listing__store", "listing__variant__product__brand")
    date_hierarchy = "valid_from"


@admin.register(NutritionRecord)
class NutritionRecordAdmin(admin.ModelAdmin):
    list_display = ("listing", "protein_g", "carbs_g", "fat_g", "valid_from", "valid_to")
    list_select_related = ("listing__store", "listing__variant__product__brand")


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ("code", "store", "discount_percent", "is_active", "last_seen_at")
    list_filter = ("store", "is_active")


@admin.register(ScrapeRun)
class ScrapeRunAdmin(admin.ModelAdmin):
    list_display = ("store", "started_at", "finished_at", "status", "items_found", "prices_changed", "errors")
    list_filter = ("store", "status")
    readonly_fields = [f.name for f in ScrapeRun._meta.fields]
