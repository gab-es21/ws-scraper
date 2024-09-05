from .firebase_setup import db

def add_coupon(brand_name, code, discount, is_percentage, is_active=True):
    code = code.upper()
    # Convert brand name to lowercase for subcollection name
    subcollection_name = brand_name.lower().replace(" ", "_")
    
    # Check if the brand exists
    brand_ref = db.collection('brands').document(subcollection_name)
    if not brand_ref.get().exists:
        print(f"Brand '{brand_name}' does not exist. Please add the brand first.")
        return

    # Add new coupon
    coupon_ref = db.collection('coupons').document(code)
    coupon_ref.set({
        'brand': brand_ref,
        'code': code,
        'discount': discount,
        'is_percentage': is_percentage,
        'is_active': is_active
    })
    print(f"Coupon '{code}' added successfully for brand '{brand_name}'.")

def update_coupon(code, new_discount=None, new_is_percentage=None, new_is_active=None):
    code = code.upper()
    coupon_ref = db.collection('coupons').document(code)
    coupon = coupon_ref.get()
    if not coupon.exists:
        print(f"Coupon with code '{code}' does not exist.")
        return

    updates = {}
    if new_discount is not None:
        updates['discount'] = new_discount
    if new_is_percentage is not None:
        updates['is_percentage'] = new_is_percentage
    if new_is_active is not None:
        updates['is_active'] = new_is_active

    if updates:
        coupon_ref.update(updates)
        print(f"Coupon '{code}' updated successfully.")
    else:
        print("No updates provided.")

def delete_coupon(code):
    code = code.upper()
    coupon_ref = db.collection('coupons').document(code)
    coupon = coupon_ref.get()
    if not coupon.exists:
        print(f"Coupon with code '{code}' does not exist.")
        return

    coupon_ref.delete()
    print(f"Coupon '{code}' deleted successfully.")
