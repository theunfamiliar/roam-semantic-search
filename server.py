from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv; load_dotenv()
import os, json, faiss, numpy as np
import httpx
import smtplib
from email.mime.text import MIMEText
import logging
import re

# ─── Set Up Logging ───
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/reindex.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    force=True
)

app = FastAPI(title="Roam Semantic Search API", version="1.0.0")

class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    page: int = 1
    per_page: int = 5
    mode: str = "Next RAP"
    rhyme_sound: str | None = None
    brain: str = "ideas"

security = HTTPBasic()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://roamresearch.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def log_routes():
    print("🔍 Registered routes:")
    for route in app.routes:
        print(f"  {route.path} -> {route.name} ({','.join(route.methods)})")

_model = None
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

USERNAME = os.getenv("USERNAME", "admin")
PASSWORD = os.getenv("PASSWORD", "secret")
ROAM_GRAPH = os.getenv("ROAM_GRAPH", "unfamiliar")
ROAM_TOKEN = os.getenv("ROAM_TOKEN")


def send_email_alert(subject: str, body: str):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = os.getenv("MAIL_FROM")
    msg["To"] = os.getenv("MAIL_TO")
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(os.getenv("MAIL_FROM"), os.getenv("MAIL_PASS"))
            server.send_message(msg)
    except Exception as e:
        print(f"❌ Email send failed: {e}")


def get_model():
    global _model
    if _model is None:
        print("→ Loading SentenceTransformer model...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username != USERNAME or credentials.password != PASSWORD:
        raise HTTPException(status_code=401, detail="Unauthorized. Use correct Basic Auth.")
    return True


def get_filenames(brain: str):
    if brain not in ("ideas", "daylist"):
        raise HTTPException(status_code=400, detail="Invalid brain")
    return {
        "index": os.path.join(DATA_DIR, f"index_{brain}.faiss"),
        "meta": os.path.join(DATA_DIR, f"metadata_{brain}.json")
    }

@app.get("/")
def root(): return JSONResponse(content={"status": "running"})

@app.get("/ping")
def ping(): return {"ping": "pong"}

@app.get("/docs")
def docs_redirect(): return {"docs": "/docs is disabled. This app runs without automatic docs."}

@app.post("/reindex")
async def reindex(auth: bool = Depends(authenticate)):
    print("🔁 TOC-based dual-brain reindex via Roam API")
    url = f"https://api.roamresearch.com/api/graph/{ROAM_GRAPH}/q"
    headers = {
        "X-Authorization": f"Bearer {ROAM_TOKEN}",
        "Content-Type": "application/json"
    }

    toc_query = {
        "query": """
        [:find ?section ?childTitle
         :where
         [?toc :node/title \"TOC\"]
         [?toc :block/children ?sec]
         [?sec :block/string ?section]
         [?sec :block/children ?child]
         [?child :block/string ?childTitle]]
        """
    }

    block_query = {
        "query": """
        [:find ?uid ?str ?parent ?page_title
         :where
         [?b :block/uid ?uid]
         [?b :block/string ?str]
         [?b :block/parents ?parent]
         [?b :block/page ?p]
         [?p :node/title ?page_title]]
        """
    }

    try:
        async with httpx.AsyncClient() as client:
            toc_res = await client.post(url, headers=headers, json=toc_query, follow_redirects=True)
            toc_res.raise_for_status()
            toc_result = toc_res.json()["result"]

            block_res = await client.post(url, headers=headers, json=block_query, follow_redirects=True)
            block_res.raise_for_status()
            raw_blocks = block_res.json()["result"]

        toc_map = {"ideas": set(), "daylist": set()}
        for section, page in toc_result:
            if section.lower() == "ideas":
                toc_map["ideas"].add(page)
            elif section.lower() == "daylist":
                toc_map["daylist"].add(page)

        blocks = [
            {"uid": uid, "string": string, "parent_uid": parent_uid, "page_title": page_title}
            for uid, string, parent_uid, page_title in raw_blocks
            if string and uid
        ]

        for brain in ["ideas", "daylist"]:
            selected = [b for b in blocks if b["page_title"] in toc_map[brain]]
            print(f"🧠 {brain} → {len(selected)} blocks")

            if not selected:
                continue

            uid_map = {b["uid"]: b for b in selected}
            parent_map = {}
            for b in selected:
                p = b["parent_uid"]
                if p: parent_map.setdefault(p, []).append(b["uid"])

            def extract_tags(t): return " ".join(re.findall(r"#\w+|\[\[.*?\]\]", t))
            def get_chunk(b):
                parent = uid_map.get(b["parent_uid"], {}).get("string", "")
                children = [uid_map[c]["string"] for c in parent_map.get(b["uid"], []) if uid_map.get(c)]
                return f"Page: {b['page_title']} {extract_tags(b['string'])} {parent} {b['string']} {' '.join(children)}".strip()

            texts = [get_chunk(b) for b in selected]
            refs = [f'(({b["uid"]}))' for b in selected]
            model = get_model()
            embeddings = model.encode(texts, batch_size=64, convert_to_numpy=True, show_progress_bar=True)
            dim = embeddings.shape[1]
            index = faiss.IndexFlatL2(dim)
            index.add(embeddings)

            metadata = []
            for i, b in enumerate(selected):
                uid = b["uid"]
                metadata.append({
                    "text": texts[i],
                    "ref": refs[i],
                    "uid": uid,
                    "parent_uid": b.get("parent_uid"),
                    "page_title": b.get("page_title"),
                    "children": [uid_map[j]["uid"] for j in parent_map.get(uid, [])],
                    "is_rap": "#raps" in texts[i].lower() or "[[raps]]" in texts[i].lower(),
                    "is_ripe": "[[ripe]]" in texts[i].lower(),
                    "near_idea": False
                })

            files = get_filenames(brain)
            faiss.write_index(index, files["index"])
            with open(files["meta"], "w", encoding="utf-8") as f:
                json.dump(metadata, f)

        return {"status": "success"}

    except Exception as e:
        logging.exception("❌ Reindex failed")
        send_email_alert("🚨 Reindex Failed", str(e))
        raise HTTPException(status_code=500, detail=str(e))

SearchRequest.model_rebuild()