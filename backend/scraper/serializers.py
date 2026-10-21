from rest_framework import serializers

from .models import Brand, Product, ScrapeRun, Store


class StoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = ["id", "slug", "name", "website"]


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ["id", "name"]


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "brand", "name", "category", "image_url"]


class ScrapeRunSerializer(serializers.ModelSerializer):
    store = serializers.CharField(source="store.name")

    class Meta:
        model = ScrapeRun
        fields = [
            "id",
            "store",
            "started_at",
            "finished_at",
            "status",
            "items_found",
            "prices_changed",
            "nutrition_changed",
            "errors",
        ]
