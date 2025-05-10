from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import os, json, faiss, numpy as np

class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    mode: str = "Next RAP"
    rhyme_sound: str | None = None

# App setup
app = FastAPI(
    title="Roam Semantic Search API",
    description="Query your Roam graph semantically using sentence-transformer embeddings + FAISS",
    version="1.0.0"
)
security = HTTPBasic()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Log all registered routes at startup
@app.on_event("startup")
async def log_routes():
    print("🔍 Registered routes:")
    for route in app.routes:
        print(f"  {route.path} -> {route.name} ({','.join(route.methods)})")

# Globals and directories
_model = None
DATA_DIR = "data"
HIDDEN_DATA_DIR = os.path.join(DATA_DIR, ".data")
PARSED_BLOCKS = os.path.join(HIDDEN_DATA_DIR, "parsed_blocks.json")
INDEX_FILE = os.path.join(DATA_DIR, "index.faiss")
METADATA_FILE = os.path.join(DATA_DIR, "metadata.json")
os.makedirs(HIDDEN_DATA_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# Load or cache model
def get_model():
    global _model
    if _model is None:
        print("→ Loading SentenceTransformer model...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

# Basic auth
def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username != "admin" or credentials.password != "secret":
        raise HTTPException(status_code=401, detail="Unauthorized. Use Basic Auth: -u admin:secret")
    return True

# Healthcheck endpoints
@app.get("/")
def root(): return JSONResponse(content={"status": "running"})
@app.get("/ping")
def ping(): return {"ping": "pong"}
@app.get("/docs")
def docs_redirect(): return {"docs": "/docs is disabled. This app runs without automatic docs."}

# Semantic search handler
def _search_semantic(request: SearchRequest):
    if not os.path.exists(INDEX_FILE) or not os.path.exists(METADATA_FILE):
        raise HTTPException(status_code=400, detail="Index not found")

    model = get_model()
    embedding = model.encode([request.query], convert_to_numpy=True)
    index = faiss.read_index(INDEX_FILE)

    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    D, I = index.search(embedding, request.top_k)
    return [metadata[i] for i in I[0] if i < len(metadata)]

@app.post("/")
@app.post("/search")
@app.post("/semantic")
def semantic_entrypoint(request: SearchRequest, auth: bool = Depends(authenticate)):
    results = _search_semantic(request)
    return {"results": results}

# Reindexing
@app.post("/reindex")
def reindex(auth: bool = Depends(authenticate)):
    if not os.path.exists(PARSED_BLOCKS):
        raise HTTPException(status_code=400, detail="parsed_blocks.json not found")

    with open(PARSED_BLOCKS, "r", encoding="utf-8") as f:
        blocks = json.load(f)

    valid_blocks = [b for b in blocks if b.get("string") and b.get("uid")]
    if not valid_blocks:
        raise HTTPException(status_code=400, detail="No valid blocks to index")

    texts = [b["string"].strip() for b in valid_blocks]
    refs = [f'(({b["uid"]}))' for b in valid_blocks]

    model = get_model()
    embeddings = model.encode(texts, batch_size=64, convert_to_numpy=True, show_progress_bar=True)
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    uid_to_index = {b["uid"]: i for i, b in enumerate(valid_blocks)}
    parent_map = {}
    for i, b in enumerate(valid_blocks):
        parent = b.get("parent_uid")
        if parent and parent in uid_to_index:
            parent_map.setdefault(parent, []).append(i)

    metadata = []
    for i, b in enumerate(valid_blocks):
        uid = b["uid"]
        metadata.append({
            "text": texts[i],
            "ref": refs[i],
            "uid": uid,
            "parent_uid": b.get("parent_uid"),
            "children": [valid_blocks[j]["uid"] for j in parent_map.get(uid, [])],
            "is_rap": "#raps" in texts[i].lower() or "[[raps]]" in texts[i].lower(),
            "near_idea": False
        })

    faiss.write_index(index, INDEX_FILE)
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f)

    return {"status": "success", "indexed": len(texts)}

# Fix Pydantic v2
SearchRequest.model_rebuild()