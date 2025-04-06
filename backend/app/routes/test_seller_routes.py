import requests

BASE = "http://127.0.0.1:5000"

def pretty(res):
    print(f"Status: {res.status_code}")
    try:
        print(res.json())
    except:
        print(res.text)

# Step 1: Register Seller
def register_seller():
    print("\n🧑 Registering new seller...")
    payload = {
        "username": "ebay_laptop_dealer",
        "email": "dealer@laptopstore.com",
        "password": "sellerpass123",
        "role": "seller"
    }
    res = requests.post(f"{BASE}/auth/register", json=payload)
    pretty(res)

# Step 2: Login Seller
def login_seller():
    print("\n🔐 Logging in seller...")
    payload = {
        "email": "dealer@laptopstore.com",
        "password": "sellerpass123"
    }
    res = requests.post(f"{BASE}/auth/login", json=payload)
    pretty(res)
    return res.json().get("token")

# Step 3: Add Items (MacBook + Dell)
def add_item(token, title, brand, model, ram, storage):
    print(f"\n➕ Adding item: {title}")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "subcategory_id": 1,  # Laptops
        "title": title,
        "description": f"{title} for professionals",
        "brand": brand,
        "model": model,
        "condition": "New",
        "attributes": [
            {"attribute_id": 4, "value": ram},
            {"attribute_id": 5, "value": storage}
        ]
    }
    res = requests.post(f"{BASE}/seller/add-item", headers=headers, json=payload)
    pretty(res)
    return res.json().get("item_id")

# Step 4: Seller filters his own items
def seller_search_items(token):
    print("\n🔍 Seller filters his own items...")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "only_my_items": True,
        "filters": {
            "Brand": ["Apple"],
            "Condition": ["New"],
            "attributes": {
                "RAM": ["16GB"]
            }
        }
    }
    res = requests.post(f"{BASE}/public/browse/search-items", headers=headers, json=payload)
    pretty(res)

# Step 5: Public Search (Buyer-like)
def public_search_items():
    print("\n🌐 Public search for laptops with 512GB SSD...")
    payload = {
        "filters": {
            "Condition": ["New"],
            "attributes": {
                "Storage": ["512GB SSD"]
            }
        }
    }
    res = requests.post(f"{BASE}/public/browse/search-items", json=payload)
    pretty(res)

# Step 6: Browse Subcategory Items (e.g., Laptops)
def browse_subcategory_items():
    print("\n📂 Public browse items in subcategory Laptops...")
    res = requests.get(f"{BASE}/public/browse/items/1")  # SubcategoryID = 1
    pretty(res)

# Run the full flow
def run():
    register_seller()
    token = login_seller()

    if not token:
        print("❌ Seller login failed.")
        return

    add_item(token, "MacBook Pro M2", "Apple", "M2 2023", "16GB", "512GB SSD")
    add_item(token, "Dell XPS 15", "Dell", "XPS 9520", "32GB", "1TB SSD")

    seller_search_items(token)
    public_search_items()
    browse_subcategory_items()

if __name__ == "__main__":
    run()
