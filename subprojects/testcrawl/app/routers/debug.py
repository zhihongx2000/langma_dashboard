from fastapi import APIRouter, Depends, Query

from app.deps import verify_admin_api_key
from app.services.browser_use_adapter import check_llm_connectivity
from app.services.section_discovery import discover_sections_with_report

router = APIRouter(prefix="/api/debug", tags=["debug"])


@router.get("/discover-sections", dependencies=[Depends(verify_admin_api_key)])
def debug_discover_sections(
    url: str = Query(..., min_length=8),
    limit: int = Query(default=8, ge=1, le=50),
    timeout: int = Query(default=20, ge=5, le=120),
):
    return discover_sections_with_report(home_url=url, timeout=timeout, limit=limit)


@router.get("/llm-check", dependencies=[Depends(verify_admin_api_key)])
def debug_llm_check(prompt: str = Query(default="Reply with OK only.", min_length=2, max_length=500)):
    return check_llm_connectivity(prompt=prompt)
