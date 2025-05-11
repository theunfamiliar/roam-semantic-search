import json
import os
import datetime
from uuid import uuid4
import subprocess

INPUT_PATH = "data/graph.json"
OUTPUT_PATH = "data/.data/parsed_blocks.json"
EMAIL = "james@dunndealpr.com"

def send_email(subject, message):
    subprocess.run([
        "mail", "-s", subject, EMAIL
    ], input=message.encode(), check=False)

def main():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n📦 Starting graph import at {now}")

    if not os.path.exists(INPUT_PATH):
        print(f"❌ File not found: {INPUT_PATH}")
        send_email("❌ Graph Import Failed: File Not Found", f"graph.json was missing at {now}.")
        return

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)

    print(f"📦 Loaded {len(raw)} raw blocks")
    converted = []
    for entry in raw:
        if "string" in entry and entry["string"].strip():
            converted.append({
                "uid": str(uuid4())[:8],
                "string": entry["string"].strip(),
                "parent_uid": entry.get("parent_uid")
            })

    if not converted:
        print("❌ No valid blocks found")
        send_email("❌ Graph Import Failed: No Valid Blocks", f"graph.json had no valid blocks at {now}.")
        return

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(converted, f, ensure_ascii=False, indent=2)

    print(f"✅ Converted {len(converted)} valid blocks")
    print(f"💾 Saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
