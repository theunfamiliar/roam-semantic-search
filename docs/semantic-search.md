- ## **✅ Current Architecture (May 28, 2025)**
    - **FastAPI + Uvicorn** running on **Contabo VPS**, exposed via Nginx + HTTPS on roam.boomerjihad.com
    - Dual-brain semantic index split via Roam TOC: TOC - ideas (personal) and TOC - marketing (staff-facing)
    - Semantic reindex logic fetches data via Roam's live API, not static graph files
    - /reindex endpoint parses entire graph:
        - Blocks under TOC = foundational
        - Blocks referencing TOC = secondary
    - Each brain has:
        - FAISS .faiss index
        - .json metadata file
    - SmartBlock JS injects inline query using {{query-singularity}}
    - Queries hit /semantic, return GPT summary + sourced blocks
    - Systemd keeps semantic-api.service running 24/7
- ## **📛 Roam JS Escape Hazards**
    - ### **❌ Problem: Backtick Fence Corruption**
        - Roam Research **breaks JavaScript** if code is pasted into triple-backtick fenced blocks:
            - **Triggers corruption**:
        - ```plain text
          ```js
          window.roamAlphaAPI...
          `
          `````
            - Roam parses Markdown and splits strings unpredictably.
    - ### **✅ Fix: Safe JavaScript Injection**
        - To prevent issues:
            - ✅ Use /javascript block, **not triple backticks**.
            - ✅ Paste JS **directly into Roam's block editor**.
            - ✅ Avoid " + "" + "" + "`" patterns.
    - ### **🔍 Regex Protection in Query Filter**
        - Your Datalog filter includes:
        - ```plain text
          [:find ?uid ?str
           :where
           [?b :block/string ?str]
           [?b :block/uid ?uid]
           [(clojure.string/includes? ?str "{{query-singularity:")]
           (not [(clojure.string/includes? ?str "
          ```")])]
          ```
        - This **excludes any Roam block containing triple backticks**, avoiding malformed strings during semantic query parsing.
- ## **🧠 Confirmed Working**
    - ✅ Live API connected to Roam, uses X-Authorization headers
    - ✅ Dual-brain indexing working
    - ✅ SmartBlock + JS injection in Roam safe
    - ✅ TLS secured via Nginx + Certbot
    - ✅ Automatic port 8000 unblocking on restart
    - ✅ Pre-deploy checks via scripts/deploy.sh
    - ✅ Auth protected endpoints: /reindex, /search, /semantic
    - ✅ GPT summarization fallback safe with try/catch
- ## **🚀 Next Steps (Finalizing Robustness)**
    - ### **🐳 Containerization (Docker)**
        - Build Dockerfile for FastAPI app
        - Add docker-compose.yml with Nginx reverse proxy
        - Containerize FAISS index mount points
        - Map .env securely via Docker secrets or volume
    - ### **✅ CI/CD (GitHub Actions)**
        - Set up .github/workflows/deploy.yml to trigger scripts/deploy.sh
        - SSH into VPS and run git pull, restart systemd
    - ### **🧠 Conversational Query Interceptor**
        - Parse freeform queries with GPT to route intent
        - Add semantic fallback when no direct match found
    - ### **🧩 GPT Query Memory**
        - Store prior semantic queries + blocks returned
        - Link follow-up queries via block references
    - ### **🧠 Writeback to Roam**
        - Format output with GPT then POST back to Roam block
        - Auto-tag with #queried, #from-query, etc.
    - ### **🧠 Staff-Facing Biz Brain Interface**
        - Build web UI for querying brain=work from browser
        - Add GPT instructions for summarizing company insights
    - ### **🔐 Security**
        - Rotate admin:secret creds
        - Lock FastAPI to localhost
        - Only expose Nginx layer externally
    - ### **📈 Health Monitoring**
        - Add /healthz endpoint
        - Log startup/shutdown + errors to /logs/
        - Email alerts via Gmail SMTP still active
- ## **🗂 Final Notes**
    - ❌ No more static Roam graph exports
    - ✅ All queries run live from Roam API via HTTP
    - ✅ SmartBlock is stable
    - ✅ Systemd handles restarts
    - ❌ No nightly cron jobs
    - Last synced: **May 28, 2025**
