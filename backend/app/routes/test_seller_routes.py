import requests

BASE_URL = "http://127.0.0.1:5000"

def safe_print_response(response):
    print("Status:", response.status_code)
    try:
        print("→", response.json())
    except Exception:
        print("❌ Non-JSON response:", response.text)

# ---------- 1. Register Seller ----------
def register_seller():
    print("\n🔹 Registering seller...")
    response = requests.post(f"{BASE_URL}/auth/register", json={
        "username": "test_seller",
        "email": "test_seller@example.com",
        "password": "test123",
        "role": "seller"
    })
    safe_print_response(response)

# ---------- 2. Login Seller ----------
def login_seller():
    print("\n🔹 Logging in seller...")
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "test_seller@example.com",
        "password": "test123"
    })
    try:
        data = response.json()
        print("→", data)
        return data.get("token")
    except Exception:
        print("❌ Failed to log in:", response.text)
        return None

# ---------- 3. Test Seller APIs ----------
def test_seller_routes(token):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # ADD ITEM
    print("\n🔹 Adding item...")
    add_item = requests.post(f"{BASE_URL}/seller/add-item", headers=headers, json={
        "subcategory_id": 1,  # Ensure this exists in your DB!
        "title": "Test Laptop",
        "description": "Test desc",
        "brand": "TestBrand",
        "model": "X123",
        "condition": "New"
    })
    safe_print_response(add_item)
    try:
        item_id = add_item.json().get("item_id")
    except:
        return print("❌ Item creation failed. Exiting...")

    # VIEW ITEMS
    print("\n🔹 Viewing seller items...")
    items = requests.get(f"{BASE_URL}/seller/my-items", headers=headers)
    safe_print_response(items)

    # UPDATE ITEM
    print("\n🔹 Updating item...")
    update_item = requests.put(f"{BASE_URL}/seller/update-item/{item_id}", headers=headers, json={
        "description": "Updated description"
    })
    safe_print_response(update_item)

    # ADD ATTRIBUTE
    print("\n🔹 Adding attribute to subcategory...")
    add_attr = requests.post(f"{BASE_URL}/seller/add-attribute", headers=headers, json={
        "subcategory_id": 1,
        "name": "Storage"
    })
    safe_print_response(add_attr)
    try:
        attribute_id = add_attr.json().get("attribute_id")
    except:
        return print("❌ Attribute creation failed. Exiting...")

    # ADD ITEM ATTRIBUTE VALUE
    print("\n🔹 Adding attribute value...")
    add_attr_val = requests.post(f"{BASE_URL}/seller/add-item-attribute", headers=headers, json={
        "item_id": item_id,
        "attribute_id": attribute_id,
        "value": "256GB"
    })
    safe_print_response(add_attr_val)

    # UPDATE ATTRIBUTE VALUE (uses item_id + attribute_id)
    print("\n🔹 Updating attribute value...")
    update_attr_val = requests.put(
        f"{BASE_URL}/seller/update-item-attribute/{item_id}/{attribute_id}",
        headers=headers,
        json={"value": "32GB"}
    )
    safe_print_response(update_attr_val)

    # DELETE ATTRIBUTE VALUE (uses item_id + attribute_id)
    print("\n🔹 Deleting attribute value...")
    delete_attr_val = requests.delete(
        f"{BASE_URL}/seller/delete-item-attribute/{item_id}/{attribute_id}",
        headers=headers
    )
    safe_print_response(delete_attr_val)

    # DELETE ITEM
    print("\n🔹 Deleting item...")
    delete_item = requests.delete(f"{BASE_URL}/seller/delete-item/{item_id}", headers=headers)
    safe_print_response(delete_item)

# ---------- Run Test ----------
if __name__ == "__main__":
    register_seller()
    token = login_seller()
    if token:
        test_seller_routes(token)
    else:
        print("❌ Could not authenticate seller.")
