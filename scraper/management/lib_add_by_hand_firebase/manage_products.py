import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta
import hashlib

# Initialize Firebase
cred = credentials.Certificate('./cred/serviceAccount.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

def hash_url(url):
    return hashlib.sha256(url.encode('utf-8')).hexdigest()

def add_or_update_product(brand_name, category_name, product_name, image_url, product_url, weight, carbs_percentage, fat_percentage, protein_percentage, price, historical_prices=None):
    brand_ref = db.collection('brands').document(brand_name.lower().replace(" ", "_"))
    
    if not brand_ref.get().exists:
        print(f"Brand '{brand_name}' does not exist.")
        return

    category_ref = db.collection('categories').document(category_name.lower().replace(" ", "_"))
    if not category_ref.get().exists:
        print(f"Category '{category_name}' does not exist.")
        return
    
    product_id = f"{brand_name.lower()}_{product_name.lower().replace(' ', '_')}"
    product_ref = db.collection('products').document(product_id)
    
    # Check if product exists
    if not product_ref.get().exists:
        product_ref.set({
            'brand': brand_ref,
            'category': category_ref,
            'name': product_name,
            'image_url': image_url,
            'product_url': product_url,
            'weight': weight,
            'carbs_percentage': carbs_percentage,
            'fat_percentage': fat_percentage,
            'protein_percentage': protein_percentage,
            'is_available': True
        })
        print(f"Added new product '{product_name}' under brand '{brand_name}' and category '{category_name}'.")
    else:
        # Update product details if it already exists
        product_ref.update({
            'weight': weight,
            'carbs_percentage': carbs_percentage,
            'fat_percentage': fat_percentage,
            'protein_percentage': protein_percentage,
        })
    
    # Update latest price
    latest_price_ref = product_ref.collection('latest_price').document('latest')
    latest_price_ref.set({
        'price': price,
        'last_updated': datetime.utcnow()
    })
    
    # Add to price history if not already present for today
    if historical_prices is None:
        historical_prices = []
    
    today = datetime.utcnow().date()
    price_history_ref = product_ref.collection('price_history')
    existing_today = price_history_ref.where('date', '==', today.isoformat()).stream()
    if not any(existing_today):
        price_history_ref.add({'price': price, 'date': today.isoformat()})
    
    for historical_price in historical_prices:
        if isinstance(historical_price['date'], datetime):
            historical_price_date = historical_price['date'].date().isoformat()
        else:
            historical_price_date = historical_price['date'].isoformat()
        
        existing_date = price_history_ref.where('date', '==', historical_price_date).stream()
        if not any(existing_date):
            price_history_ref.add({'price': historical_price['price'], 'date': historical_price_date})
    
    # Update or add to product_links collection
    product_link_id = hash_url(product_url)
    product_link_ref = brand_ref.collection('product_links').document(product_link_id)
    product_link_ref.set({
        'link': product_url,
        'last_updated': datetime.utcnow(),
        'category': category_ref
    }, merge=True)
    
    print(f"Updated price for product '{product_name}'. Current price: {price}")

def main():
    brand_name = "Prozis"
    
    sample_products = [
        {
            'category_name': "Whey Protein",
            'product_name': "Whey Protein 1kg",
            'image_url': "https://example.com/product_image_1.jpg",
            'product_url': "https://example.com/product_page_1",
            'weight': "1000g",
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
            'weight': "1000g",
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
            'weight': "1000g",
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
            'weight': "500g",
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
    main()
