from rest_framework import viewsets
from .models import Brand, Product, Price
from .serializers import BrandSerializer, ProductSerializer, PriceSerializer
from django.shortcuts import render

class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

class PriceViewSet(viewsets.ModelViewSet):
    queryset = Price.objects.all()
    serializer_class = PriceSerializer

def index(request):
    return render(request, 'index.html')
