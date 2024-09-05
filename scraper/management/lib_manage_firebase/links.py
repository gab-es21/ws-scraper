from datetime import datetime
import urllib.parse
from .firebase_setup import db

def encode_link(link):
    return urllib.parse.quote(link, safe='')

def add_or_update_link(link, subcollection, brand_name, category=None):
    links_ref = db.collection('links').document(subcollection).collection('items').document(encode_link(link))
    data = {
        'link': link,
        'brand': db.collection('brands').document(brand_name.lower().replace(" ", "_")),
        'last_updated': datetime.utcnow(),
    }
    if category:
        data['category'] = db.collection('categories').document(category.lower().replace(" ", "_"))

    links_ref.set(data, merge=True)
    print(f"Added/Updated {subcollection[:-1]} link: {link}")

def list_links(subcollection):
    links_ref = db.collection('links').document(subcollection).collection('items')
    links = links_ref.stream()
    
    print(f"{subcollection.capitalize()} links:")
    for link in links:
        link_data = link.to_dict()
        brand_ref = link_data.get('brand')
        brand_name = brand_ref.id if brand_ref else "Unknown"
        category_ref = link_data.get('category')
        category_name = category_ref.id if category_ref else "Unknown"
        print(f"Link: {link_data.get('link')}, Brand: {brand_name}, Category: {category_name}, Last Updated: {link_data.get('last_updated')}")

def delete_link(link, subcollection):
    links_ref = db.collection('links').document(subcollection).collection('items').document(encode_link(link))
    
    if links_ref.get().exists:
        links_ref.delete()
        print(f"Deleted {subcollection[:-1]} link: {link}")
    else:
        print(f"{subcollection[:-1].capitalize()} link '{link}' not found.")
