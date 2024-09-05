import os
import django
from django.utils import timezone
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workoutsavings.settings_local')
django.setup()

from scraper.models import Brand, Product, Flavor, Quantity, ProductVariant, Price, NutritionalValue, Coupon, HistoricalPrice

# Create Brands
brands = ['Prozis', 'My Protein', 'Zumub', 'Gold Nutrition', 'Decathlon']
brand_objects = [Brand(name=brand_name) for brand_name in brands]
Brand.objects.bulk_create(brand_objects)

# Create Products
products_data = [
    {'brand': 'Prozis', 'name': 'Whey Protein', 'image_url': 'http://example.com/whey.jpg', 'product_url': 'http://example.com/whey'},
    {'brand': 'My Protein', 'name': 'Impact Whey', 'image_url': 'http://example.com/impact.jpg', 'product_url': 'http://example.com/impact'},
    # Add more products as needed
]

product_objects = []
for data in products_data:
    brand = Brand.objects.get(name=data['brand'])
    product, created = Product.objects.get_or_create(
        brand=brand,
        name=data['name'],
        defaults={'image_url': data['image_url'], 'product_url': data['product_url']}
    )
    if not created:
        product.is_available = True  # Mark product as available if found again
        product.save()
    product_objects.append(product)

# Create Flavors
flavors = ['Vanilla', 'Chocolate', 'Strawberry']
flavor_objects = [Flavor(name=flavor_name) for flavor_name in flavors]
Flavor.objects.bulk_create(flavor_objects)

# Create Quantities
quantities = [500, 1000, 2000]
quantity_objects = [Quantity(amount_g=qty) for qty in quantities]
Quantity.objects.bulk_create(quantity_objects)

# Create ProductVariants
product_variants_data = [
    {'product': 'Whey Protein', 'flavor': 'Vanilla', 'quantity': 500},
    {'product': 'Impact Whey', 'flavor': 'Chocolate', 'quantity': 1000},
    # Add more product variants as needed
]

product_variant_objects = []
for data in product_variants_data:
    product = Product.objects.get(name=data['product'])
    flavor = Flavor.objects.get(name=data['flavor'])
    quantity = Quantity.objects.get(amount_g=data['quantity'])
    variant, created = ProductVariant.objects.get_or_create(
        product=product,
        flavor=flavor,
        quantity=quantity
    )
    product_variant_objects.append(variant)

# Create Prices and HistoricalPrices
prices_data = [
    {'product_variant': 'Whey Protein - Vanilla - 500g', 'normal_price': 20.0},
    {'product_variant': 'Impact Whey - Chocolate - 1000g', 'normal_price': 35.0},
    # Add more price data as needed
]

price_objects = []
for data in prices_data:
    product_name, flavor_name, quantity_str = data['product_variant'].split(' - ')
    product_variant = ProductVariant.objects.get(
        product__name=product_name,
        flavor__name=flavor_name,
        quantity__amount_g=int(quantity_str.replace('g', ''))
    )
    price = Price.objects.create(
        product_variant=product_variant,
        normal_price=data['normal_price']
    )
    price_objects.append(price)

    # Create 10 historical prices
    for i in range(10):
        HistoricalPrice.objects.create(
            product_variant=product_variant,
            normal_price=data['normal_price'] - i * 0.5,  # Decrease price for history
            date=timezone.now() - timedelta(days=i)
        )

# Create Nutritional Values
nutritional_data = [
    {'product_variant': 'Whey Protein - Vanilla - 500g', 'carbs_percentage': 5.0, 'fat_percentage': 8.0, 'protein_percentage': 80.0},
    {'product_variant': 'Impact Whey - Chocolate - 1000g', 'carbs_percentage': 4.0, 'fat_percentage': 6.0, 'protein_percentage': 82.0},
    # Add more nutritional data as needed
]

nutritional_value_objects = []
for data in nutritional_data:
    product_name, flavor_name, quantity_str = data['product_variant'].split(' - ')
    product_variant = ProductVariant.objects.get(
        product__name=product_name,
        flavor__name=flavor_name,
        quantity__amount_g=int(quantity_str.replace('g', ''))
    )
    nutritional_value = NutritionalValue.objects.create(
        product_variant=product_variant,
        carbs_percentage=data['carbs_percentage'],
        fat_percentage=data['fat_percentage'],
        protein_percentage=data['protein_percentage']
    )
    nutritional_value_objects.append(nutritional_value)

# Create Coupons
coupons_data = [
    {'brand': 'Prozis', 'code': 'PROZIS20', 'discount': 20.0, 'is_active': True},
    {'brand': 'My Protein', 'code': 'MYPROTEIN25', 'discount': 25.0, 'is_active': False},
    # Add more coupon data as needed
]

coupon_objects = [Coupon(brand=Brand.objects.get(name=data['brand']), code=data['code'], discount=data['discount'], is_active=data['is_active']) for data in coupons_data]
Coupon.objects.bulk_create(coupon_objects)

# Mark products that were not found during scraping as unavailable
Product.objects.filter(is_available=False).update(is_available=False)
