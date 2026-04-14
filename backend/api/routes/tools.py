from __future__ import annotations

from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import RedirectResponse

from backend.config.settings import get_settings


router = APIRouter(prefix="/tools", tags=["tools"])


def _get_crawler_base_url() -> str:
    return (get_settings().education_exam_crawler_base_url or "").strip().rstrip("/")


def _build_tools_error(detail: str, action: str) -> dict[str, str]:
    return {
        "code": "TOOL_NOT_CONFIGURED",
        "detail": detail,
        "action": action,
    }


def _is_crawler_reachable(base_url: str) -> bool:
    if not base_url:
        return False
    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"}:
        return False
    health_url = f"{base_url}/health"
    request = Request(health_url, method="GET")
    try:
        with urlopen(request, timeout=1.5) as response:
            return 200 <= response.status < 500
    except (URLError, TimeoutError, ValueError):
        return False


@router.get("/education-exam-crawler/status")
def education_exam_crawler_status() -> dict[str, str | bool]:
    base_url = _get_crawler_base_url()
    configured = bool(base_url)
    reachable = _is_crawler_reachable(base_url) if configured else False
    if not configured:
        message = "考试院信息收集工具未配置，请先复制 .env.example 为 .env 并填写配置。"
    elif not reachable:
        message = "考试院信息收集工具服务未启动，请先启动 8001 端口服务。"
    else:
        message = "考试院信息收集工具可用。"
    return {
        "configured": configured,
        "reachable": reachable,
        "launch_url": f"{base_url}/" if configured else "",
        "message": message,
    }


@router.get("/education-exam-crawler/launch", include_in_schema=False)
def launch_education_exam_crawler() -> RedirectResponse:
    base_url = _get_crawler_base_url()
    if not base_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=_build_tools_error(
                "考试院信息收集工具未配置，暂时无法跳转。",
                "复制 .env.example 为 .env，并设置 EDUCATION_EXAM_CRAWLER_BASE_URL=http://127.0.0.1:8001",
            ),
        )

    return RedirectResponse(url=f"{base_url}/", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
