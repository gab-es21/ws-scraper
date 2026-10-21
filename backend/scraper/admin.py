from django.contrib import admin

from .models import Brand, Coupon, Flavor, HistoricalPrice, NutritionalValue, Price, Product, ProductVariant, Quantity


class PriceAdmin(admin.ModelAdmin):
    list_display = ("product_variant", "normal_price", "price_per_100g", "price_per_100g_protein")


class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "brand_display", "product_url")

    def brand_display(self, obj):
        return obj.brand.name

    brand_display.short_description = "Brand"


admin.site.register(Brand)
admin.site.register(Product, ProductAdmin)
admin.site.register(Flavor)
admin.site.register(Quantity)
admin.site.register(ProductVariant)
admin.site.register(Price, PriceAdmin)
admin.site.register(NutritionalValue)
admin.site.register(Coupon)
admin.site.register(HistoricalPrice)
