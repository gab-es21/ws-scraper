import os

from django.db.models import Prefetch
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Brand, Listing, NutritionRecord, PriceRecord, Product, Store, price_per_100g
from .serializers import BrandSerializer, ProductSerializer, StoreSerializer
from .tasks import get_products_info, save_to_db


class StoreViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Store.objects.order_by("name")
    serializer_class = StoreSerializer


class BrandViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Brand.objects.order_by("name")
    serializer_class = BrandSerializer


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProductSerializer

    def get_queryset(self):
        products = Product.objects.order_by("name")
        brand = self.request.query_params.get("brand")
        if brand:
            products = products.filter(brand_id=brand)
        return products


@api_view(["GET"])
def extraction_status(request):
    """Every listing with its current price, nutrition and when it was last checked."""
    listings = (
        Listing.objects.select_related("store", "variant__product__brand")
        .prefetch_related(
            Prefetch("price_records", PriceRecord.objects.filter(valid_to__isnull=True), to_attr="current_prices"),
            Prefetch(
                "nutrition_records",
                NutritionRecord.objects.filter(valid_to__isnull=True),
                to_attr="current_nutritions",
            ),
        )
        .order_by("variant__product__brand__name", "variant__product__name", "variant__flavor", "variant__size_g")
    )

    data = []
    for listing in listings:
        variant, product = listing.variant, listing.variant.product
        price = listing.current_prices[0] if listing.current_prices else None
        nutrition = listing.current_nutritions[0] if listing.current_nutritions else None
        data.append(
            {
                "id": listing.id,
                "store": listing.store.name,
                "brand": product.brand.name,
                "name": product.name,
                "flavor": variant.flavor,
                "weight_g": variant.size_g,
                "price_eur": price.price if price else None,
                "price_per_100g": price_per_100g(price.price, variant.size_g) if price else None,
                "is_available": bool(price and price.in_stock and listing.is_active),
                "last_extracted": price.last_checked_at if price else None,
                "product_url": listing.url,
                "protein_g": nutrition.protein_g if nutrition else None,
                "fat_g": nutrition.fat_g if nutrition else None,
                "carbs_g": nutrition.carbs_g if nutrition else None,
            }
        )
    return Response(data)


@api_view(["POST"])
def run_extraction(request):
    """Trigger extraction on all saved link files and save results to DB."""
    links_dir = "links"
    all_files = [f for f in os.listdir(links_dir) if f.startswith("prozis") and f.endswith(".json")]

    if not all_files:
        return Response({"error": "No link files found in links/"}, status=404)

    products = get_products_info(all_files)

    saved, failed = [], []
    for p in products:
        try:
            save_to_db(p)
            saved.append(p["name"])
        except Exception as e:
            failed.append({"name": p.get("name"), "error": str(e)})

    return Response(
        {
            "files_processed": len(all_files),
            "extracted": len(products),
            "saved": len(saved),
            "failed": failed,
        }
    )
