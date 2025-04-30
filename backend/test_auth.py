import requests
import json

# Base URL
BASE_URL = "http://localhost:8000/api/v1"

def login():
    """Try to log in and get a token"""
    credentials = {
        "username": "test@example.com",
        "password": "test123"
    }
    
    # Try both potential login endpoints
    endpoints = [
        "/login/access-token",
        "/auth/login",
        "/login"
    ]
    
    for endpoint in endpoints:
        try:
            print(f"Trying login endpoint: {endpoint}")
            response = requests.post(f"{BASE_URL}{endpoint}", data=credentials)
            print(f"Response: {response.status_code}")
            print(response.text)
            
            if response.status_code == 200:
                token_data = response.json()
                if "access_token" in token_data:
                    return token_data["access_token"]
                else:
                    print("No access_token found in response")
        except Exception as e:
            print(f"Error during login: {e}")
    
    return None

def create_summary(token):
    """Try to create a summary"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "original_text": "This is a test text that needs to be summarized. It should be at least fifty characters long to meet the minimum length requirement specified in the schema definition. This is a test text that needs to be summarized.",
        "model_id": "bart-cnn",
        "max_length": 150,
        "min_length": 50
    }
    
    try:
        response = requests.post(f"{BASE_URL}/summaries/", headers=headers, json=data)
        print(f"Status code: {response.status_code}")
        print(response.text)
    except Exception as e:
        print(f"Error creating summary: {e}")

if __name__ == "__main__":
    token = login()
    if token:
        print(f"Logged in successfully, token: {token[:10]}...")
        create_summary(token)
    else:
        print("Failed to log in, cannot test summary creation")