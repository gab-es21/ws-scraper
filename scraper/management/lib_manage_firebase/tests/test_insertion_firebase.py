from datetime import datetime, timedelta
from ..categories import add_or_update_category, list_categories, delete_category
from ..coupons import add_coupon, update_coupon, delete_coupon
from ..links import add_or_update_link, list_links, delete_link
from ..products import add_or_update_product

#wip

def test_categories():
    categories = ["Whey Protein", "Casein Protein", "Vegan Protein", "Creatine"]

    # Adding categories
    for category in categories:
        add_or_update_category(category)
    
    # Listing categories
    list_categories()
    
    # Deleting a category
    delete_category("Creatine")
    
    # Listing categories after deletion
    list_categories()

def test_coupons():
    # Adding coupons
    add_coupon('MyProtein', 'SAVE10', 10.0, True)
    add_coupon('Prozis', 'PROZIS20', 20.0, True)
    add_coupon('Gold Nutrition', 'GOLD5', 5.0, False)

    # Updating a coupon
    update_coupon('SAVE10', new_discount=12.5, new_is_active=False)

    # Deleting a coupon
    delete_coupon('GOLD5')

def test_links():
    brand_name = "Prozis"
    
    # Add or update links
    add_or_update_link("https://www.prozis.com/pt/pt", "search_links", brand_name)
    add_or_update_link("https://www.prozis.com/pt/pt/nutricao-desportiva/proteina/proteina-whey", "search_links", brand_name, "Whey Protein")
    add_or_update_link("https://www.prozis.com/pt/pt/nutricao-desportiva/proteina/caseina-e-proteina-de-absorcao-lenta", "search_links", brand_name, "Casein Protein")
    add_or_update_link("https://www.prozis.com/pt/pt/nutricao-desportiva/proteina/proteina-vegetal", "search_links", brand_name, "Vegan Protein")
    add_or_update_link("https://www.prozis.com/pt/pt/nutricao-desportiva/desenvolvimento-muscular/creatina", "search_links", brand_name, "Creatine")
    
    # List links
    list_links('search_links')
    list_links('product_links')
    
    # Delete a link
    delete_link("https://www.prozis.com/pt/pt", 'search_links')
    delete_link("https://www.prozis.com/pt/pt/nutricao-desportiva/proteina/proteina-vegetal", 'product_links')
    
    # List links after deletion
    list_links('search_links')
    list_links('product_links')

def test_products():
    brand_name = "Prozis"
    
    sample_products = [
        {
            'category_name': "Whey Protein",
            'product_name': "Whey Protein 1kg",
            'image_url': "https://example.com/product_image_1.jpg",
            'product_url': "https://example.com/product_page_1",
            'weight': 1000,
            'carbs_percentage': 5.0,
            'fat_percentage': 3.0,
            'protein_percentage': 90.0,
            'price': 19.99,
            'historical_prices': [
                {'price': 21.99, 'date': datetime.utcnow() - timedelta(days=10)},
                {'price': 20.99, 'date': datetime.utcnow() - timedelta(days=5)},
                {'price': 19.99, 'date': datetime.utcnow()}
            ]
        },
        {
            'category_name': "Casein Protein",
            'product_name': "Casein Protein 1kg",
            'image_url': "https://example.com/product_image_2.jpg",
            'product_url': "https://example.com/product_page_2",
            'weight': 1000,
            'carbs_percentage': 4.0,
            'fat_percentage': 2.5,
            'protein_percentage': 92.0,
            'price': 22.99,
            'historical_prices': [
                {'price': 24.99, 'date': datetime.utcnow() - timedelta(days=15)},
                {'price': 23.99, 'date': datetime.utcnow() - timedelta(days=7)},
                {'price': 22.99, 'date': datetime.utcnow()}
            ]
        },
        {
            'category_name': "Vegan Protein",
            'product_name': "Vegan Protein 1kg",
            'image_url': "https://example.com/product_image_3.jpg",
            'product_url': "https://example.com/product_page_3",
            'weight': 1000,
            'carbs_percentage': 6.0,
            'fat_percentage': 3.0,
            'protein_percentage': 85.0,
            'price': 24.99,
            'historical_prices': [
                {'price': 26.99, 'date': datetime.utcnow() - timedelta(days=20)},
                {'price': 25.99, 'date': datetime.utcnow() - timedelta(days=10)},
                {'price': 24.99, 'date': datetime.utcnow()}
            ]
        },
        {
            'category_name': "Creatine",
            'product_name': "Creatine 500g",
            'image_url': "https://example.com/product_image_4.jpg",
            'product_url': "https://example.com/product_page_4",
            'weight': 500,
            'carbs_percentage': 0.0,
            'fat_percentage': 0.0,
            'protein_percentage': 0.0,
            'price': 14.99,
            'historical_prices': [
                {'price': 16.99, 'date': datetime.utcnow() - timedelta(days=30)},
                {'price': 15.99, 'date': datetime.utcnow() - timedelta(days=20)},
                {'price': 14.99, 'date': datetime.utcnow()}
            ]
        }
    ]
    
    for product in sample_products:
        add_or_update_product(
            brand_name,
            product['category_name'],
            product['product_name'],
            product['image_url'],
            product['product_url'],
            product['weight'],
            product['carbs_percentage'],
            product['fat_percentage'],
            product['protein_percentage'],
            product['price'],
            product['historical_prices']
        )

if __name__ == "__main__":
    test_categories()
    test_coupons()
    test_links()
    test_products()
