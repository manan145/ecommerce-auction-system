import requests

BASE_URL = "http://127.0.0.1:5000"

# Admin credentials
admin_credentials = {
    "email": "admin1@example.com",
    "password": "admin123"
}

# Authenticate and get token
def get_admin_jwt():
    response = requests.post(f"{BASE_URL}/auth/login", json=admin_credentials)
    if response.status_code == 200:
        access_token = response.json().get("token")
        print("🔑 Access Token:", access_token)  # Debugging log
        return f"Bearer {access_token}"
    else:
        raise Exception(f"Login failed: {response.status_code} → {response.text}")


# Attribute data for each subcategory
attribute_map = {
    "Laptops": [
        "Processor", "RAM", "Storage", "Screen Size", "Graphics Card",
        "Operating System", "Battery Life", "Weight", "Warranty"
    ],
    "Smartphones": [
        "Storage", "RAM", "Color", "Operating System", "Screen Size",
        "Camera", "Battery Capacity", "Network Support", "Warranty"
    ],
    "Audio Accessories": [
        "Type", "Wireless", "Noise Cancellation", "Battery Life",
        "Charging Port", "Color", "Mic Included", "Waterproof Rating", "Warranty"
    ],
    "Monitors": [
        "Screen Size", "Resolution", "Panel Type", "Refresh Rate", "Ports",
        "Response Time", "Aspect Ratio", "Adjustable Stand", "VESA Mount Support", "Warranty"
    ]
}




def add_attributes_for_subcategory(name, attributes, headers):
    print(f"\n🔹 Adding attributes for Subcategory ID {name}...")
    print("Headers:", headers)  # Debugging log
    response = requests.post(
        f"{BASE_URL}/admin/add-attributes",
        headers=headers,
        json={
            "subcategory_name": name,
            "attributes": attributes
        }
    )
    try:
        print("Status:", response.status_code)
        print("→", response.json())
    except:
        print("❌ Failed to parse response:", response.text)


# Main script execution
if __name__ == "__main__":
    try:
        token = get_admin_jwt()
        headers = {
            "Authorization": token,
            "Content-Type": "application/json"
        }

        for subcategory_id, attr_list in attribute_map.items():
            add_attributes_for_subcategory(subcategory_id, attr_list, headers)

    except Exception as e:
        print("❌ Error:", e)
