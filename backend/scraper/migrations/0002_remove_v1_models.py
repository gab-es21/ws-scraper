"""
Drop the v1 schema (Brand/Product/ProductVariant/Price/HistoricalPrice/...).

The v1 tables only held a single scrape run; 0003 creates the v2 schema
(stores, listings, change-only price and nutrition records) from scratch.
"""

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("scraper", "0001_initial"),
    ]

    operations = [
        migrations.DeleteModel(name="HistoricalPrice"),
        migrations.DeleteModel(name="Coupon"),
        migrations.DeleteModel(name="Price"),
        migrations.DeleteModel(name="NutritionalValue"),
        migrations.DeleteModel(name="ProductVariant"),
        migrations.DeleteModel(name="Quantity"),
        migrations.DeleteModel(name="Flavor"),
        migrations.DeleteModel(name="Product"),
        migrations.DeleteModel(name="Brand"),
    ]
