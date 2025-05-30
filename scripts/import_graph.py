import json
import os
import datetime
from uuid import uuid4

INPUT_PATH = "data/graph.json"
OUTPUT_PATH = "data/.data/parsed_blocks.json"

def parse_blocks(blocks):
    result = []

    def traverse(block, parent_uid=None):
        if "string" in block and block["string"].strip():
            result.append({
                "uid": block.get("uid", str(uuid4())[:8]),
                "string": block["string"].strip(),
                "parent_uid": parent_uid
            })
        for child in block.get("children", []):
            traverse(child, block.get("uid"))

    for block in blocks:
        traverse(block)

    return result

def main():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n📦 Starting graph import at {now}")

    if not os.path.exists(INPUT_PATH):
        print(f"❌ File not found: {INPUT_PATH}")
        return

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)

    print(f"📦 Loaded {len(raw)} raw blocks")
    converted = parse_blocks(raw)

    if not converted:
        print("❌ No valid blocks found")
        return

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(converted, f, ensure_ascii=False, indent=2)

    print(f"✅ Converted {len(converted)} valid blocks")
    print(f"💾 Saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()