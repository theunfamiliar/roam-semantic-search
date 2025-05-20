import os
import requests
from dotenv import load_dotenv

# 🔁 Load the .env variables
load_dotenv()

# 🔑 Use your actual Roam API token
token = os.getenv("ROAM_API_TOKEN")

# 🔒 Explicit graph name (hardcoded)
graph = "unfamiliar"

# ✅ Check if token loaded correctly
if not token:
    raise ValueError("Missing ROAM_API_TOKEN from environment variables.")

# 📦 Datalog query to test
query = {
    "query": "[ :find ?uid :where [?b :block/uid ?uid] ]"
}

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# 🌐 Construct exact API endpoint
url = "https://api.roamresearch.com/api/graph/unfamiliar/datalog"

# 🚀 Send request
res = requests.post(url, headers=headers, json=query)

# 🧪 Print result
if res.status_code == 200:
    print("✅ Roam API connected successfully!")
    print(res.json())
else:
    print(f"❌ API error {res.status_code}:")
    print(res.text)