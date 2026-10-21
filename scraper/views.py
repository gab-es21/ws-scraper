import os

from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Brand, Price, Product
from .serializers import BrandSerializer, PriceSerializer, ProductSerializer
from .tasks import get_products_info, save_to_db


class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class PriceViewSet(viewsets.ModelViewSet):
    queryset = Price.objects.all()
    serializer_class = PriceSerializer


@api_view(["GET"])
def extraction_status(request):
    """Return every product with its current price and last extraction time."""
    rows = Price.objects.select_related(
        "product_variant__product__brand",
        "product_variant__quantity",
    ).order_by("product_variant__product__brand__name", "product_variant__product__name")

    data = []
    for price in rows:
        pv = price.product_variant
        product = pv.product
        try:
            nv = pv.nutritional_value
            protein = nv.protein_percentage
            fat = nv.fat_percentage
            carbs = nv.carbs_percentage
            # 0/0/0 means the data was never successfully extracted
            if protein == 0 and fat == 0 and carbs == 0:
                protein = fat = carbs = None
        except Exception:
            protein = fat = carbs = None
        data.append(
            {
                "id": product.id,
                "name": product.name,
                "brand": product.brand.name,
                "weight_g": pv.quantity.amount_g,
                "price_eur": price.normal_price,
                "price_per_100g": round(price.price_per_100g, 2),
                "is_available": product.is_available,
                "last_extracted": price.last_updated,
                "product_url": product.product_url,
                "protein_g": protein,
                "fat_g": fat,
                "carbs_g": carbs,
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


def index(request):
    return render(request, "index.html")
