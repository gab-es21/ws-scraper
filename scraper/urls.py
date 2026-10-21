from django.urls import include, path
from django.views.generic import TemplateView
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"brands", views.BrandViewSet)
router.register(r"products", views.ProductViewSet)
router.register(r"prices", views.PriceViewSet)

urlpatterns = [
    path("api/", include(router.urls)),
    path("api/extraction-status/", views.extraction_status),
    path("api/run-extraction/", views.run_extraction),
    path("", TemplateView.as_view(template_name="index.html"), name="index"),
]
