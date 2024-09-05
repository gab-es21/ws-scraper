from datetime import datetime, timedelta
import hashlib
from .firebase_setup import db

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

def delete_product(product_id):
    product_ref = db.collection('products').document(product_id)
    
    if not product_ref.get().exists:
        print(f"Product with ID '{product_id}' does not exist.")
        return

    # Delete product and its subcollections
    price_history_ref = product_ref.collection('price_history')
    for doc in price_history_ref.stream():
        doc.reference.delete()

    latest_price_ref = product_ref.collection('latest_price').document('latest')
    if latest_price_ref.get().exists:
        latest_price_ref.delete()
    
    product_ref.delete()
    print(f"Product with ID '{product_id}' deleted successfully.")

def list_products():
    products_ref = db.collection('products')
    products = products_ref.stream()
    
    print("Products:")
    for product in products:
        product_data = product.to_dict()
        brand_ref = product_data.get('brand')
        brand_name = brand_ref.id if brand_ref else "Unknown"
        category_ref = product_data.get('category')
        category_name = category_ref.id if category_ref else "Unknown"
        print(f"Product ID: {product.id}, Name: {product_data.get('name')}, Brand: {brand_name}, Category: {category_name}")
