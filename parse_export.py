import os
import json
import uuid

INPUT_FILE = "data/roam_export.json"
OUTPUT_FILE = "data/parsed_blocks.json"

def extract_blocks(nodes, depth=0, ancestors=None):
    blocks = []
    ancestors = ancestors or []

    for node in nodes:
        string = node.get("string", "").strip()
        uid = node.get("uid", str(uuid.uuid4())[:9])

        # Flag this block if it directly contains a rap tag
        is_rap = "#raps" in string or "[[raps]]" in string

        # Flag this block or any of its ancestors as being 'near idea'
        has_idea = "#idea" in string or "[[idea]]" in string
        near_idea = has_idea or any("#idea" in a or "[[idea]]" in a for a in ancestors)

        block = {
            "string": string,
            "uid": uid,
            "depth": depth,
            "is_rap": is_rap,
            "near_idea": near_idea,
        }

        if string:
            blocks.append(block)

        if "children" in node:
            blocks.extend(extract_blocks(node["children"], depth + 1, ancestors + [string]))

    return blocks

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ File not found: {INPUT_FILE}")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)

    if isinstance(raw, dict) and "pages" in raw:
        pages = raw["pages"]
    elif isinstance(raw, list):
        pages = raw
    else:
        print("❌ Invalid export format. Expected list or dict with 'pages'.")
        return

    blocks = []
    for page in pages:
        blocks.extend(extract_blocks(page.get("children", [])))

    print(f"✅ Extracted {len(blocks)} blocks.")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(blocks, f, indent=2)

if __name__ == "__main__":
    main()