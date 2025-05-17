import os
import smtplib
import requests
from email.message import EmailMessage

GMAIL_USER = "316promoteam@gmail.com"
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")
TO_EMAIL = "james@dunndealpr.com"

def send_alert_email(subject, body):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = GMAIL_USER
    msg["To"] = TO_EMAIL
    msg.set_content(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_PASSWORD)
        server.send_message(msg)

try:
    response = requests.post(
        "http://localhost:8000/search",
        auth=("admin", "secret"),
        json={"query": "test", "top_k": 1}
    )
    if response.status_code == 200:
        print("✅ Search successful")
    else:
        print("❌ Search failed:", response.status_code)
        send_alert_email("🚨 Search Endpoint Failed", f"Status: {response.status_code}\nResponse: {response.text}")
except Exception as e:
    print("❌ Search raised an exception:", e)
    send_alert_email("🚨 Search Exception", str(e))