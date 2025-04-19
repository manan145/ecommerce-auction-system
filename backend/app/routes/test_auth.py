import requests

BASE_URL = "http://127.0.0.1:5000"

new_user = {
    "username": "kshah",
    "email": "kshah@example.com",
    "password": "securepass",
    "role": "buyer"
}

# Function to register user
def register_user():
    print("📦 Registering new user...")
    response = requests.post(f"{BASE_URL}/auth/register", json=new_user)
    print("Status:", response.status_code)
    try:
        print("→", response.json())
    except:
        print("❌ Failed to parse response:", response.text)

    if response.status_code == 201:
        print("✅ User registered successfully!")
    elif response.status_code == 409:
        print("⚠️ Email already exists.")
    else:
        print("❌ Failed to register user.")

# Function to login the new user
def login_user():
    print("\n🔑 Logging in with new user credentials...")
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "email": new_user['email'],
        "password": new_user['password']
    })

    print("Status:", response.status_code)
    try:
        data = response.json()
        print("→", data)
    except:
        print("❌ Failed to parse response:", response.text)
        return

    if response.status_code == 200:
        token = data.get("token")
        print("✅ Login successful. Token:", token)
        return f"Bearer {token}"
    else:
        print("❌ Login failed.")
        return None

# Main test script
if __name__ == "__main__":
    register_user()
    login_user()
