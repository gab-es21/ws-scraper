import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase
cred = credentials.Certificate('./cred/serviceAccount.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

def add_or_update_category(name):
    category_ref = db.collection('categories').document(name.lower().replace(" ", "_"))
    
    if category_ref.get().exists:
        print(f"Category '{name}' already exists.")
    else:
        category_ref.set({
            'name': name,
        })
        print(f"Added category '{name}'.")

def list_categories():
    categories_ref = db.collection('categories')
    categories = categories_ref.stream()
    
    print("Categories:")
    for category in categories:
        print(f"Name: {category.to_dict().get('name')}")

def delete_category(name):
    category_ref = db.collection('categories').document(name.lower().replace(" ", "_"))
    
    if category_ref.get().exists:
        category_ref.delete()
        print(f"Deleted category '{name}'.")
    else:
        print(f"Category '{name}' not found.")

def main():
    categories = [
        "Whey Protein", 
        "Casein Protein", 
        "Vegan Protein", 
        "Creatine", 
        #"Pre-Workout", 
        #"BCAAs", 
        #"Multivitamins", 
        #"Omega-3"
    ]
    
    # Adding categories
    for category in categories:
        add_or_update_category(category)
    
    # Listing categories
    list_categories()
    
    # Example of deleting a category
    # delete_category("Omega-3")
    
    # Listing categories after deletion
    # list_categories()

if __name__ == "__main__":
    main()
