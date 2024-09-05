import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase
cred = credentials.Certificate('./cred/serviceAccount.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

def add_brand(name, website_url):
    # Convert brand name to lowercase for subcollection name
    subcollection_name = name.lower().replace(" ", "_")

    # Check if the brand already exists
    brands_ref = db.collection('brands')
    query = brands_ref.where('name', '==', name).get()
    if query:
        print(f"Brand '{name}' already exists.")
        return

    # Add new brand
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

def main():
    # Example usage
    add_brand('MyProtein', 'https://www.myprotein.com')
    add_brand('Prozis', 'https://www.prozis.com')
    add_brand('Zumub', 'https://www.zumub.com')
    add_brand('Gold Nutrition', 'https://www.goldnutrition.com')

    # Assuming you have the brand subcollection name, you can update or delete a brand
    # You can retrieve brand subcollection name from Firestore console or through a query
    #subcollection_name = 'myprotein'  # replace with the actual brand subcollection name

    #update_brand(subcollection_name, new_name='New Brand Name', new_website_url='https://www.newbrandwebsite.com')
    #delete_brand(subcollection_name)

if __name__ == "__main__":
    main()
