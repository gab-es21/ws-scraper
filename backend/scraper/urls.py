from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"stores", views.StoreViewSet)
router.register(r"brands", views.BrandViewSet)
router.register(r"products", views.ProductViewSet, basename="product")

urlpatterns = [
    path("api/", include(router.urls)),
    path("api/extraction-status/", views.extraction_status),
    path("api/run-extraction/", views.run_extraction),
]
