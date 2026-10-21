from django.db import models
from django.utils import timezone


class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    id = models.AutoField(primary_key=True)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    image_url = models.URLField(max_length=200)
    product_url = models.URLField(max_length=200)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Flavor(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Quantity(models.Model):
    amount_g = models.FloatField()

    def __str__(self):
        return f"{self.amount_g}g"


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.ForeignKey(Quantity, on_delete=models.CASCADE)
    flavor = models.ForeignKey(Flavor, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.product.name} - {self.flavor.name} - {self.quantity.amount_g}g"


class NutritionalValue(models.Model):
    product_variant = models.OneToOneField(ProductVariant, on_delete=models.CASCADE, related_name="nutritional_value")
    carbs_percentage = models.FloatField()
    fat_percentage = models.FloatField()
    protein_percentage = models.FloatField()

    def __str__(self):
        return f"Nutritional values for {self.product_variant}"


class Price(models.Model):
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name="prices")
    normal_price = models.FloatField()
    last_updated = models.DateTimeField(auto_now=True)

    @property
    def price_per_100g(self):
        return self.normal_price / (self.product_variant.quantity.amount_g / 100)

    @property
    def price_per_100g_protein(self):
        protein_percentage = self.product_variant.nutritional_value.protein_percentage
        return self.price_per_100g / (protein_percentage / 100)

    def save(self, *args, **kwargs):
        # Add the current price to the history before saving the new price
        if self.pk:
            HistoricalPrice.objects.create(
                product_variant=self.product_variant, normal_price=self.normal_price, date=timezone.now()
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Price for {self.product_variant}"


class Coupon(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    code = models.CharField(max_length=100)
    discount = models.FloatField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} - {self.brand.name}"


class HistoricalPrice(models.Model):
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name="historical_prices")
    normal_price = models.FloatField()
    date = models.DateTimeField()

    def __str__(self):
        return f"{self.date} - {self.product_variant}"
