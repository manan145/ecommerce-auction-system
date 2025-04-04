import requests

BASE_URL = "http://127.0.0.1:5000"

# Replace with a valid JWT token for your admin user
ADMIN_JWT = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc0MzczNzk3NCwianRpIjoiZjEzY2RhNDUtYjdmNi00MWMzLWFlZGYtOWI5YWZjNjFlYzgzIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjQiLCJuYmYiOjE3NDM3Mzc5NzQsImNzcmYiOiI0MjNlNWI0ZC1hNzg0LTRlY2MtODZiMS1iNjg5MWNjMzQyNmMiLCJleHAiOjE3NDM3Mzg4NzR9.VHdT2mSBkqU5SsauL1qlojY8YuUCpSDo4I_ULaJqcIo"

headers = {
    "Authorization": ADMIN_JWT,
    "Content-Type": "application/json"
}

# Attribute data for each subcategory
attribute_map = {
    1: [  # Laptops
        "Processor", "RAM", "Storage", "Screen Size", "Graphics Card",
        "Operating System", "Battery Life", "Weight", "Warranty"
    ],
    2: [  # Smartphones
        "Storage", "RAM", "Color", "Operating System", "Screen Size",
        "Camera", "Battery Capacity", "Network Support", "Warranty"
    ],
    3: [  # Audio Accessories
        "Type", "Wireless", "Noise Cancellation", "Battery Life",
        "Charging Port", "Color", "Mic Included", "Waterproof Rating", "Warranty"
    ],
    4: [  # Monitors
        "Screen Size", "Resolution", "Panel Type", "Refresh Rate", "Ports",
        "Response Time", "Aspect Ratio", "Adjustable Stand", "VESA Mount Support", "Warranty"
    ]
}


def add_attributes_for_subcategory(subcategory_id, attributes):
    print(f"\n🔹 Adding attributes for Subcategory ID {subcategory_id}...")
    response = requests.post(
        f"{BASE_URL}/admin/add-attributes",
        headers=headers,
        json={
            "subcategory_id": subcategory_id,
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
    for subcategory_id, attr_list in attribute_map.items():
        add_attributes_for_subcategory(subcategory_id, attr_list)
