# ... all previous import and setup code remains unchanged ...

@app.post("/reindex")
async def reindex(auth: bool = Depends(authenticate)):
    print("🔁 TOC-based dual-brain reindex via Roam API")
    url = f"https://api.roamresearch.com/api/graph/{ROAM_GRAPH}/q"
    headers = {
        "X-Authorization": f"Bearer {ROAM_TOKEN}",  # ✅ FIXED HERE
        "Content-Type": "application/json"
    }

    toc_query = {
        "query": """
        [:find ?section ?childTitle
         :where
         [?toc :node/title "TOC"]
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