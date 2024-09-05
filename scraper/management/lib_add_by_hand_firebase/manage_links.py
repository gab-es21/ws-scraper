import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import urllib.parse


# Initialize Firebase
cred = credentials.Certificate('./cred/serviceAccount.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

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

def main():
    brand_name = "Prozis"
    # Add or update links
    add_or_update_link("https://www.prozis.com/pt/pt/nutricao-desportiva/proteina/proteina-whey", "search_links", brand_name, "Whey Protein")
    add_or_update_link("https://www.prozis.com/pt/pt/nutricao-desportiva/proteina/caseina-e-proteina-de-absorcao-lenta", "search_links", brand_name, "Casein Protein")
    add_or_update_link("https://www.prozis.com/pt/pt/nutricao-desportiva/proteina/proteina-vegetal", "search_links", brand_name, "Vegan Protein")
    add_or_update_link("https://www.prozis.com/pt/pt/nutricao-desportiva/desenvolvimento-muscular/creatina", "search_links", brand_name, "Creatine")

    brand_name = "Zumub"
    # Add or update links
    add_or_update_link("https://www.zumub.com/PT/proteinas/whey", "search_links", brand_name, "Whey Protein")
    add_or_update_link("https://www.zumub.com/PT/proteinas/caseina", "search_links", brand_name, "Casein Protein")
    add_or_update_link("https://www.zumub.com/PT/proteinas/proteina-vegetal", "search_links", brand_name, "Vegan Protein")
    add_or_update_link("https://www.zumub.com/PT/creatina", "search_links", brand_name, "Creatine")

    brand_name = "My Protein"
    # Add or update links
    add_or_update_link("https://www.myprotein.pt/nutrition/protein/whey-protein.list", "search_links", brand_name, "Whey Protein")
    add_or_update_link("https://www.myprotein.pt/nutrition/protein.list?pageNumber=1&facetFilters=pt_protein_content:Casein+and+Milk+Proteins", "search_links", brand_name, "Casein Protein")
    add_or_update_link("https://www.myprotein.pt/nutrition/protein/vegan-protein.list", "search_links", brand_name, "Vegan Protein")
    add_or_update_link("https://www.myprotein.pt/nutrition/creatine.list", "search_links", brand_name, "Creatine")

    # List links
    list_links('search_links')
    list_links('product_links')
    
    # Delete a link
    # delete_link("https://www.prozis.com/pt/pt", 'search_links')
    # delete_link("https://www.prozis.com/pt/pt/nutricao-desportiva/proteina/proteina-vegetal", 'product_links')
    
    # List links after deletion
    list_links('search_links')
    list_links('product_links')

if __name__ == "__main__":
    main()
