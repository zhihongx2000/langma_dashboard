from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.province import Province
from app.services.score_query import get_score_query_url
from app.services.chat_assistant import chat_completion, summarize_policy_document
from app.services.sichuan_assistant import answer_from_crawled_content
from app.services.sichuan_levels import get_level3_content, get_sichuan_levels
from app.services.gansu_levels import get_gansu_levels
from app.services.gansu2_levels import get_gansu2_levels
from app.services.guangdong1_levels import get_guangdong1_levels
from app.services.guangdong2_levels import get_guangdong2_levels
from app.services.chongqing_levels import get_chongqing_levels
from app.services.guangxi_levels import get_guangxi_levels
from app.services.shanghai_levels import get_shanghai_levels
from app.services.beijing_levels import get_beijing_levels
from app.services.anhui_levels import get_anhui_levels
from app.services.hainan_levels import get_hainan_levels
from app.services.henan1_levels import get_henan1_levels
from app.services.henan2_levels import get_henan2_levels
from app.services.neimenggu1_levels import get_neimenggu1_levels
from app.services.neimenggu2_levels import get_neimenggu2_levels
from app.services.heilongjiang_levels import get_heilongjiang_levels
from app.services.hebei_levels import get_hebei_levels
from app.services.hubei_levels import get_hubei_levels
from app.services.hunan_levels import get_hunan_levels
from app.services.fujian_levels import get_fujian_levels
from app.services.guizhou_levels import get_guizhou_levels
from app.services.jiangsu_levels import get_jiangsu_levels
from app.services.jilin_levels import get_jilin_levels
from app.services.jiangxi_levels import get_jiangxi_levels
from app.services.liaoning1_levels import get_liaoning1_levels
from app.services.liaoning2_levels import get_liaoning2_levels
from app.services.ningxia_levels import get_ningxia_levels
from app.services.qinghai_levels import get_qinghai_levels
from app.services.tianjin_levels import get_tianjin_levels
from app.services.shandong_levels import get_shandong_levels
from app.services.shaanxi_levels import get_shaanxi_levels
from app.services.shanxi_levels import get_shanxi_levels
from app.services.xinjiang_levels import get_xinjiang_levels
from app.services.xizang_levels import get_xizang_levels
from app.services.yunnan_levels import get_yunnan_levels
from app.services.zhejiang_levels import get_zhejiang_levels

router = APIRouter(prefix="/api/test", tags=["test-local"])


class AssistantRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)
    province_id: int = Field(default=1, ge=1)


class ChatMessage(BaseModel):
    role: str = Field(..., min_length=1, max_length=32)
    content: str = Field(..., min_length=1, max_length=12000)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(..., min_length=1, max_length=60)


class SummarizePolicyRequest(BaseModel):
    content: str = Field(..., min_length=10, max_length=120000)
    title: str | None = Field(default=None, max_length=500)


@router.get("/sichuan/levels")
def sichuan_levels():
    return get_sichuan_levels()


@router.get("/sichuan/content")
def sichuan_content(url: str = Query(..., min_length=10)):
    return get_level3_content(url)


@router.get("/page/content")
def page_content(url: str = Query(..., min_length=10)):
    """Endpoint doc."""
    return get_level3_content(url)


@router.get("/heilongjiang/levels")
def heilongjiang_levels():
    """Endpoint doc."""
    return get_heilongjiang_levels()


@router.get("/jiangsu/levels")
def jiangsu_levels():
    """Endpoint doc."""
    return get_jiangsu_levels()


@router.get("/gansu/levels")
def gansu_levels():
    """Endpoint doc."""
    return get_gansu_levels()


@router.get("/gansu2/levels")
def gansu2_levels():
    """Endpoint doc."""
    return get_gansu2_levels()


@router.get("/hainan/levels")
def hainan_levels():
    """Endpoint doc."""
    return get_hainan_levels()


@router.get("/qinghai/levels")
def qinghai_levels():
    """Endpoint doc."""
    return get_qinghai_levels()


@router.get("/neimenggu1/levels")
def neimenggu1_levels():
    """Endpoint doc."""
    return get_neimenggu1_levels()


@router.get("/neimenggu2/levels")
def neimenggu2_levels():
    """Endpoint doc."""
    return get_neimenggu2_levels()


@router.get("/henan1/levels")
def henan1_levels():
    """Endpoint doc."""
    return get_henan1_levels()


@router.get("/henan2/levels")
def henan2_levels():
    """Endpoint doc."""
    return get_henan2_levels()


@router.get("/jilin/levels")
def jilin_levels():
    """Endpoint doc."""
    return get_jilin_levels()


@router.get("/ningxia/levels")
def ningxia_levels():
    """Endpoint doc."""
    return get_ningxia_levels()


@router.get("/yunnan/levels")
def yunnan_levels():
    """Endpoint doc."""
    return get_yunnan_levels()


@router.get("/beijing/levels")
def beijing_levels():
    """Endpoint doc."""
    return get_beijing_levels()


@router.get("/zhejiang/levels")
def zhejiang_levels():
    """Endpoint doc."""
    return get_zhejiang_levels()


@router.get("/tianjin/levels")
def tianjin_levels():
    """Endpoint doc."""
    return get_tianjin_levels()


@router.get("/hebei/levels")
def hebei_levels():
    """Endpoint doc."""
    return get_hebei_levels()


@router.get("/shandong/levels")
def shandong_levels():
    """Endpoint doc."""
    return get_shandong_levels()


@router.get("/chongqing/levels")
def chongqing_levels():
    """Endpoint doc."""
    return get_chongqing_levels()


@router.get("/shaanxi/levels")
def shaanxi_levels():
    """Endpoint doc."""
    return get_shaanxi_levels()


@router.get("/shanxi/levels")
def shanxi_levels():
    """Endpoint doc."""
    return get_shanxi_levels()


@router.get("/liaoning1/levels")
def liaoning1_levels():
    """Endpoint doc."""
    return get_liaoning1_levels()


@router.get("/liaoning2/levels")
def liaoning2_levels():
    """Endpoint doc."""
    return get_liaoning2_levels()


@router.get("/jiangxi/levels")
def jiangxi_levels():
    """Endpoint doc."""
    return get_jiangxi_levels()


@router.get("/hubei/levels")
def hubei_levels():
    """Endpoint doc."""
    return get_hubei_levels()


@router.get("/hunan/levels")
def hunan_levels():
    """Endpoint doc."""
    return get_hunan_levels()


@router.get("/fujian/levels")
def fujian_levels():
    """Endpoint doc."""
    return get_fujian_levels()


@router.get("/guizhou/levels")
def guizhou_levels():
    """Endpoint doc."""
    return get_guizhou_levels()


@router.get("/guangxi/levels")
def guangxi_levels():
    """Endpoint doc."""
    return get_guangxi_levels()


@router.get("/shanghai/levels")
@router.get("/shmeea/levels")
def shanghai_levels():
    """Endpoint doc."""
    return get_shanghai_levels()


@router.get("/anhui/levels")
def anhui_levels():
    """Endpoint doc."""
    return get_anhui_levels()


@router.get("/guangdong1/levels")
def guangdong1_levels():
    """Endpoint doc."""
    return get_guangdong1_levels()


@router.get("/guangdong2/levels")
def guangdong2_levels():
    """Endpoint doc."""
    return get_guangdong2_levels()


@router.get("/xinjiang/levels")
def xinjiang_levels():
    """Endpoint doc."""
    return get_xinjiang_levels()


@router.get("/xizang/levels")
def xizang_levels():
    """Endpoint doc."""
    return get_xizang_levels()


@router.get("/score-query")
def score_query_url(
    province_id: int = Query(..., ge=1),
    display_name: str | None = Query(default=None, max_length=120),
    db: Session = Depends(get_db),
):
    province = db.get(Province, province_id)
    if not province:
        raise HTTPException(status_code=404, detail="Province not found")

    lookup = (display_name or "").strip() or province.name
    return {
        "province_id": province.id,
        "province_name": province.name,
        "score_query_url": get_score_query_url(lookup, portal_url=province.url or None),
    }


@router.post("/sichuan/assistant")
def sichuan_assistant(payload: AssistantRequest, db: Session = Depends(get_db)):
    return answer_from_crawled_content(db, payload.question, province_id=payload.province_id)


def _run_test_chat(payload: ChatRequest) -> dict:
    raw = [{"role": m.role.strip(), "content": m.content.strip()} for m in payload.messages]
    for m in raw:
        if m["role"] not in {"user", "assistant"}:
            raise HTTPException(status_code=400, detail="messages[].role 仅支持 user 或 assistant")
    return chat_completion(raw)


@router.post("/chat")
def test_chat(payload: ChatRequest):
    """Endpoint doc."""
    return _run_test_chat(payload)


@router.post("/ai/chat")
def test_chat_alias(payload: ChatRequest):
    """与 /chat 相同，便于兼容旧前端或代理路径。"""
    return _run_test_chat(payload)


@router.post("/summarize-policy")
def test_summarize_policy(payload: SummarizePolicyRequest):
    """根据第三板块正文调用专用系统提示词做自考政策整理（不写入多轮 chat history）。"""
    title = (payload.title or "").strip() or None
    return summarize_policy_document(content=payload.content.strip(), title=title)


