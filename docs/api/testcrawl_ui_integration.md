# testcrawl UI Integration

## Goal
`testcrawl` is the independent education exam crawler tool under `subprojects/testcrawl`.

The current formal crawler page is the former local test UI. The old lightweight page has been retired.

## Current entry model
- Workbench launch endpoint: `/api/v1/tools/education-exam-crawler/launch`
- testcrawl formal page: `http://127.0.0.1:8001/`
- Deprecated compatibility alias: `http://127.0.0.1:8001/test-ui`

## testcrawl structure
- `subprojects/testcrawl/app/`: API, crawler, scheduler, models
- `subprojects/testcrawl/web/index.html`: formal crawler page
- `subprojects/testcrawl/scripts/run_local_tool.ps1`: formal local launcher
- `subprojects/testcrawl/scripts/run_local_test.ps1`: local test-profile launcher

## Main routes
- `GET /` -> formal crawler page
- `GET /test-ui` -> compatibility redirect to `/`
- `GET /health` -> health check
- `GET /docs` -> OpenAPI docs

## Workbench integration notes
- Frontend button opens `/api/v1/tools/education-exam-crawler/launch`
- Backend launch target is controlled by `EDUCATION_EXAM_CRAWLER_BASE_URL`
- If the base URL is not configured, the launch endpoint returns an explicit error

## Local development
Run the tool:

```powershell
powershell -ExecutionPolicy Bypass -File .\subprojects\testcrawl\scripts\run_local_tool.ps1
```

Set the workbench env:

```env
EDUCATION_EXAM_CRAWLER_BASE_URL=http://127.0.0.1:8001
```
