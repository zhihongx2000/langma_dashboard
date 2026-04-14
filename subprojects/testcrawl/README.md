# testcrawl

Independent education exam crawler tool based on `FastAPI + SQLAlchemy + Playwright + browser-use`.

## Structure
- `app/`: API, scheduler, crawler logic, data models.
- `web/`: formal crawler page used by the workbench and local runs.
- `scripts/`: local launch and smoke scripts.
- `data/`: local databases and seed assets.

## Entry URLs
- Formal crawler page: `GET /`
- Compatibility alias: `GET /test-ui`
- API docs: `GET /docs`
- Health check: `GET /health`

## Run locally
Preferred launcher:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_local_tool.ps1
```

Default local port is `8001`. `run_local_tool.ps1` binds `0.0.0.0` so other devices on the LAN can use `http://<this-machine-ip>:8001/`. On the machine itself you can still use:
- `http://127.0.0.1:8001/`
- `http://127.0.0.1:8001/docs`
- `http://127.0.0.1:8001/health`

You can also run manually:

```bash
python -m venv .venv
. .venv/Scripts/activate
pip install -r requirements.txt
python -m playwright install chromium
copy .env.example .env
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

## Development profile
An optional local profile is still available when you want to run with `.env.localtest`:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_local_test.ps1
```

Optional smoke check:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\smoke_local_test.ps1
```

Config templates:
- `.env.example`: formal local tool config
- `.env.localtest.example`: optional local development profile
- default local databases live under `data/`

## Workbench integration
The main workbench should launch this tool through the workbench backend:

- workbench launch endpoint: `/api/v1/tools/education-exam-crawler/launch`
- target page in this tool: `/`

## Main APIs
- `GET /api/provinces`
- `GET /api/provinces/{province_id}/sections`
- `GET /api/sections/{section_id}/contents`
- `GET /api/contents/search?keyword=...`
- `GET /api/search/ai?query=...`
- `POST /api/crawl/trigger` with `X-API-Key`
- `GET /api/crawl/report-latest`
- `GET /api/crawl/report/{job_id}`

## Docker
```bash
docker compose up --build
```
