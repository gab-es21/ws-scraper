# scraper/tests.py
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient


class ProductTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_get_products(self):
        response = self.client.get(reverse("product-list"))
        self.assertEqual(response.status_code, 200)

    def test_get_product_detail(self):
        response = self.client.get(reverse("product-detail", args=["some-product-id"]))
        self.assertEqual(response.status_code, 404)  # Assuming the product doesn't exist
