from .firebase_setup import db

def add_brand(name, website_url):
    subcollection_name = name.lower().replace(" ", "_")

    brands_ref = db.collection('brands')
    query = brands_ref.where('name', '==', name).get()
    if query:
        print(f"Brand '{name}' already exists.")
        return

    new_brand_ref = brands_ref.document(subcollection_name)
    new_brand_ref.set({
        'name': name,
        'website_url': website_url
    })
    print(f"Brand '{name}' added successfully with website '{website_url}' and subcollection '{subcollection_name}'.")

def update_brand(subcollection_name, new_name=None, new_website_url=None):
    brand_ref = db.collection('brands').document(subcollection_name)
    brand = brand_ref.get()
    if not brand.exists:
        print(f"Brand with subcollection name '{subcollection_name}' does not exist.")
        return

    updates = {}
    if new_name:
        updates['name'] = new_name
    if new_website_url:
        updates['website_url'] = new_website_url

    if updates:
        brand_ref.update(updates)
        print(f"Brand '{subcollection_name}' updated successfully.")
    else:
        print("No updates provided.")

def delete_brand(subcollection_name):
    brand_ref = db.collection('brands').document(subcollection_name)
    brand = brand_ref.get()
    if not brand.exists:
        print(f"Brand with subcollection name '{subcollection_name}' does not exist.")
        return

    brand_ref.delete()
    print(f"Brand '{subcollection_name}' deleted successfully.")
