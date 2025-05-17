# scripts/verify_search_response.py

import json
import os
import time
import requests
import smtplib
from email.mime.text import MIMEText
from requests.auth import HTTPBasicAuth

BASE_URL = "http://localhost:8000"
USERNAME = os.getenv("USERNAME", "admin")
PASSWORD = os.getenv("PASSWORD", "secret")
EMAIL_TO = "james@dunndealpr.com"
EMAIL_FROM = "316promoteam@gmail.com"
SMTP_PASS = os.getenv("SMTP_PASSWORD", "")
SMTP_USER = EMAIL_FROM

def send_email(subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
    except Exception as e:
        print("❌ Failed to send email:", e)

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
        send_email(
            subject="❌ Roam Semantic Search: Verification Failed",
            body=f"The /search route failed during nightly check.\n\n{str(err)}"
        )

if __name__ == "__main__":
    verify()