import os
import json

DATA_DIR = "data"
OUTPUT_FILE = "parsed_blocks.json"

def extract_blocks_from_file(filepath):
    blocks = []
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("- ") or stripped.startswith("* "):
            blocks.append({
                "text": stripped[2:],
                "source": os.path.basename(filepath)
            })

    return blocks

def extract_all_blocks():
    all_blocks = []
    for filename in os.listdir(DATA_DIR):
        if filename.endswith(".md"):
            path = os.path.join(DATA_DIR, filename)
            blocks = extract_blocks_from_file(path)
            all_blocks.extend(blocks)

    return all_blocks

if __name__ == "__main__":
    os.makedirs(DATA_DIR, exist_ok=True)
    blocks = extract_all_blocks()
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(blocks, f, indent=2, ensure_ascii=False)

    print(f"✅ Parsed {len(blocks)} blocks from .md files.")