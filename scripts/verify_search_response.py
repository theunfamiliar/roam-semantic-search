# scripts/verify_search_response.py

import json
import os
import time
import requests
from requests.auth import HTTPBasicAuth

BASE_URL = "http://localhost:8000"
USERNAME = os.getenv("USERNAME", "admin")
PASSWORD = os.getenv("PASSWORD", "secret")

def verify():
    try:
        payload = {"query": "test", "top_k": 1}
        res = requests.post(f"{BASE_URL}/search", json=payload, auth=HTTPBasicAuth(USERNAME, PASSWORD), timeout=30)

        if res.status_code != 200:
            raise Exception(f"Status code: {res.status_code}\nBody: {res.text}")

        data = res.json()
        if "results" not in data or not data["results"]:
            raise Exception("No results found in response")

        print("✅ Search verification succeeded")
    except Exception as err:
        print("⚠️ Search verification failed")
        print(f"Error: {str(err)}")

if __name__ == "__main__":
    verify()