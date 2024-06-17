from django.urls import path
from .views import ProductList, ProductDetail, ProductFlavorHistory

urlpatterns = [
    path('products/', ProductList.as_view(), name='product-list'),
    path('products/<str:product_id>/', ProductDetail.as_view(), name='product-detail'),
    path('products/<str:product_id>/flavors/<str:flavor_id>/history/', ProductFlavorHistory.as_view(), name='product-flavor-history'),
]