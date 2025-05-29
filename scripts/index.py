from sentence_transformers import SentenceTransformer
from pathlib import Path

# Load model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Folder with your .md files
DATA_DIR = Path("./data")
EMBEDDINGS = []
CHUNKS = []

def load_md_files():
    for path in DATA_DIR.glob("*.md"):
        if path.stat().st_size == 0:
            continue  # Skip empty files
        with path.open(encoding="utf-8") as f:
            content = f.read()
            for para in content.split("\n\n"):
                text = para.strip()
                if len(text) < 10:
                    continue
                CHUNKS.append({"text": text, "source": str(path)})

def generate_embeddings():
    texts = [chunk["text"] for chunk in CHUNKS]
    return model.encode(texts, show_progress_bar=True)

def reindex():
    CHUNKS.clear()
    EMBEDDINGS.clear()
    load_md_files()
    EMBEDDINGS.extend(generate_embeddings())
    print(f"✅ Reindexed {len(CHUNKS)} chunks.")