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

security = HTTPBasic()

def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username != os.getenv("USERNAME", "admin") or credentials.password != os.getenv("PASSWORD", "secret"):
        raise HTTPException(status_code=401, detail="Unauthorized. Use correct Basic Auth.")
    return True

app = FastAPI(title="Roam Semantic Search API", version="1.0.0")

class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    page: int = 1
    per_page: int = 5
    mode: str = "Next RAP"
    rhyme_sound: str | None = None
    brain: str = "ideas"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://roamresearch.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root(): return JSONResponse(content={"status": "running"})

@app.get("/ping")
def ping(): return {"ping": "pong"}

@app.post("/reindex")
async def reindex(auth: bool = Depends(authenticate)):
    print("🔁 TOC-based tag-weighted reindexing")
    url = f"https://api.roamresearch.com/api/graph/{os.getenv('ROAM_GRAPH')}/q"
    headers = {
        "X-Authorization": f"Bearer {os.getenv('ROAM_TOKEN')}",
        "Content-Type": "application/json"
    }

    toc_titles = {
        "ideas": "TOC - ideas",
        "work": "TOC - marketing"
    }

    toc_query = {
        "query": """
        [:find ?brain ?title
         :where
         [?toc :node/title ?brain]
         [?toc :block/children ?child]
         [?child :block/string ?title]
         [(clojure.string/starts-with? ?brain "TOC -")]]
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

        brain_map = {"ideas": set(), "work": set()}
        for full_title, tag in toc_result:
            base = full_title.replace("TOC - ", "").lower()
            if base in brain_map:
                brain_map[base].add(tag)

        blocks = [
            {"uid": uid, "string": string, "parent_uid": parent_uid, "page_title": page_title}
            for uid, string, parent_uid, page_title in raw_blocks
            if string and uid and page_title != "roam/js"
        ]

        for brain, tags in brain_map.items():
            selected = []
            uid_map = {}
            for b in blocks:
                uid_map[b["uid"]] = b
                # foundational: directly in TOC
                if b["page_title"] in tags or b["string"] in tags:
                    b["__weight"] = 1.0
                    selected.append(b)
                # secondary: references a TOC page
                elif any(f"[[{tag}]]" in b["string"] or f"#{tag}" in b["string"] for tag in tags):
                    b["__weight"] = 0.5
                    selected.append(b)

            print(f"🧠 {brain} → {len(selected)} blocks")
            if not selected:
                continue

            parent_map = {}
            for b in selected:
                p = b.get("parent_uid")
                if p: parent_map.setdefault(p, []).append(b["uid"])

            def extract_tags(t): return " ".join(re.findall(r"#\w+|\[\[.*?\]\]", t))
            def get_chunk(b):
                parent = uid_map.get(b["parent_uid"], {}).get("string", "")
                children = [uid_map[c]["string"] for c in parent_map.get(b["uid"], []) if uid_map.get(c)]
                return f"Page: {b['page_title']} {extract_tags(b['string'])} {parent} {b['string']} {' '.join(children)}".strip()

            texts = [get_chunk(b) for b in selected]
            refs = [f'(({b["uid"]}))' for b in selected]
            weights = [b["__weight"] for b in selected]
            model = get_model()
            embeddings = model.encode(texts, batch_size=64, convert_to_numpy=True, show_progress_bar=True)
            embeddings *= np.array(weights)[:, None]

            dim = embeddings.shape[1]
            index = faiss.IndexFlatL2(dim)
            index.add(embeddings)

            metadata = []
            for i, b in enumerate(selected):
                metadata.append({
                    "text": texts[i],
                    "ref": refs[i],
                    "uid": b["uid"],
                    "parent_uid": b.get("parent_uid"),
                    "page_title": b.get("page_title"),
                    "children": [uid_map[j]["uid"] for j in parent_map.get(b["uid"], [])],
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
        raise HTTPException(status_code=500, detail=str(e))

SearchRequest.model_rebuild()