# testcrawl

Education exam crawler dashboard project based on `FastAPI + SQLAlchemy + Playwright + browser-use`.

## What is implemented
- Left dashboard flow: `Province -> Section -> Content`.
- Right dashboard flow: `Keyword Search + AI Search`.
- Persistent storage: crawled data is saved and can be viewed anytime.
- Manual refresh: trigger full crawl from UI or API.
- Auto refresh: full crawl every day at `12:00` (configurable).
- Refresh report: view what changed after updates (`new/modified/deleted`).

## Run locally
```bash
python -m venv .venv
. .venv/Scripts/activate
pip install -r requirements.txt
python -m playwright install chromium
copy .env.example .env
uvicorn app.main:app --reload
```

Open:
- `http://127.0.0.1:8000/` dashboard UI
- `http://127.0.0.1:8000/docs` API docs
- `http://127.0.0.1:8000/health` health check

## Local test version (one-command)
Use the local test profile:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_local_test.ps1
```

Optional smoke check (run while server is up):

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\smoke_local_test.ps1
```

Config template:
- `.env.localtest.example`
- copy to `.env.localtest` and fill keys if needed

## Main APIs
- `GET /api/provinces`
- `GET /api/provinces/{province_id}/sections`
- `GET /api/sections/{section_id}/contents`
- `GET /api/contents/search?keyword=...`
- `GET /api/search/ai?query=...`
- `POST /api/crawl/trigger` (admin key required)
- `GET /api/crawl/report-latest`
- `GET /api/crawl/report/{job_id}`

## Auto refresh config
```env
AUTO_REFRESH_ENABLED=true
AUTO_REFRESH_HOUR=12
AUTO_REFRESH_MINUTE=0
AUTO_REFRESH_TIMEZONE=Asia/Shanghai
```

## AI Search config (DeepSeek)
```env
DEEPSEEK_API_KEY=
DEEPSEEK_API_BASE_URL=https://api.deepseek.com/v1
AI_SEARCH_MODEL=deepseek-chat
AI_SEARCH_CANDIDATES=120
AI_SEARCH_LIMIT=20
```

AI prompt is tuned for:
- role: `考试院信息助手`
- task: provide self-study exam information from exam authority websites
- output: strict JSON with ranked content IDs

## browser-use config
```env
OPENAI_API_KEY=
OPENAI_BASE_URL=
BROWSER_USE_ENABLED=false
BROWSER_USE_MODEL=gpt-5-mini
BROWSER_USE_MAX_STEPS=8
BROWSER_USE_RESULT_LIMIT=8
BROWSER_USE_MIN_RESULTS_TRIGGER=3
```

## Admin auth
```http
X-API-Key: <ADMIN_API_KEY>
```

## Docker
```bash
docker compose up --build
```
