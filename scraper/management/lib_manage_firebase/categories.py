from .firebase_setup import db

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
