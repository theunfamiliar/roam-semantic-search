# fix_parsed_blocks.py

import json
from uuid import uuid4

# Read the original file
with open("data/parsed_blocks.json", "r", encoding="utf-8") as f:
    raw = json.load(f)

# Convert to required format
converted = []
for entry in raw:
    if "text" in entry:
        converted.append({
            "uid": str(uuid4())[:8],
            "string": entry["text"],
            "parent_uid": None
        })

# Save the new format back to the same file
with open("data/parsed_blocks.json", "w", encoding="utf-8") as f:
    json.dump(converted, f, ensure_ascii=False, indent=2)