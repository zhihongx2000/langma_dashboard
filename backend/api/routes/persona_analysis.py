from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.domain.enums import AnalysisModuleKey, SourceType
from backend.config.settings import get_settings
from backend.schemas.common import ApiResponse, build_response
from backend.schemas.persona_analysis import (
    ActivatePromptVersionRequest,
    AnalysisResultData,
    AnalyzeRequest,
    CreateFolderRequest,
    CreatePromptVersionRequest,
    CreateSessionRequest,
    DeleteItemResponseData,
    ImportTextRequest,
    ItemResponseData,
    ModelOptionsResponseData,
    PromptVersionItemResponseData,
    PromptVersionListResponseData,
    SessionImportResponseData,
    SessionMessagesResponseData,
    SidebarResponseData,
    UpdateFolderRequest,
    UpdatePromptVersionRequest,
    UpdateSessionRequest,
)
from backend.services.analysis_service import build_analysis_result, create_pending_analysis
from backend.services.conversation_service import (
    create_folder,
    create_session,
    delete_folder,
    delete_session,
    get_session_messages,
    get_session_or_404,
    import_text_as_session,
    list_sidebar,
    update_folder,
    update_session,
)
from backend.services.model_service import list_model_options
from backend.services.prompt_service import (
    activate_prompt_version,
    create_prompt_version,
    get_prompt_version_by_id,
    list_prompt_versions,
    update_prompt_version,
)


router = APIRouter(prefix="/persona-analysis", tags=["persona-analysis"])
ALLOWED_TEXT_EXTENSIONS = {".txt", ".csv", ".json", ".md", ".log"}


@router.get("/sidebar", response_model=ApiResponse[SidebarResponseData])
def get_sidebar(db: Session = Depends(get_db)) -> ApiResponse[SidebarResponseData]:
    return build_response(list_sidebar(db))


@router.post("/folders", response_model=ApiResponse[ItemResponseData])
def create_folder_route(
    payload: CreateFolderRequest,
    db: Session = Depends(get_db),
) -> ApiResponse[ItemResponseData]:
    return build_response(create_folder(db, payload.title, payload.is_pinned))


@router.patch("/folders/{folder_id}", response_model=ApiResponse[ItemResponseData])
def update_folder_route(
    folder_id: str,
    payload: UpdateFolderRequest,
    db: Session = Depends(get_db),
) -> ApiResponse[ItemResponseData]:
    return build_response(update_folder(db, folder_id, payload.title, payload.is_pinned))


@router.delete("/folders/{folder_id}", response_model=ApiResponse[DeleteItemResponseData])
def delete_folder_route(
    folder_id: str,
    db: Session = Depends(get_db),
) -> ApiResponse[DeleteItemResponseData]:
    return build_response(delete_folder(db, folder_id))


@router.post("/sessions", response_model=ApiResponse[ItemResponseData])
def create_session_route(
    payload: CreateSessionRequest,
    db: Session = Depends(get_db),
) -> ApiResponse[ItemResponseData]:
    return build_response(create_session(db, payload.title, payload.folder_id, payload.is_pinned))


@router.post("/sessions/import-text", response_model=ApiResponse[SessionImportResponseData])
def import_text_route(
    payload: ImportTextRequest,
    db: Session = Depends(get_db),
) -> ApiResponse[SessionImportResponseData]:
    response = import_text_as_session(
        db,
        raw_text=payload.raw_text,
        title=payload.title,
        folder_id=payload.folder_id,
        source_type=payload.source_type,
        original_file_name=None,
        mime_type="text/plain",
        auto_analyze=payload.auto_analyze,
        model_key=payload.model_key,
        prompt_version_id=payload.prompt_version_id,
    )
    return build_response(response)


@router.patch("/sessions/{session_id}", response_model=ApiResponse[ItemResponseData])
def update_session_route(
    session_id: str,
    payload: UpdateSessionRequest,
    db: Session = Depends(get_db),
) -> ApiResponse[ItemResponseData]:
    return build_response(update_session(db, session_id, payload.title, payload.is_pinned, payload.folder_id))


@router.delete("/sessions/{session_id}", response_model=ApiResponse[DeleteItemResponseData])
def delete_session_route(
    session_id: str,
    db: Session = Depends(get_db),
) -> ApiResponse[DeleteItemResponseData]:
    return build_response(delete_session(db, session_id))


@router.post("/folders/{folder_id}/uploads", response_model=ApiResponse[SessionImportResponseData])
async def upload_chat_record_route(
    folder_id: str,
    file: UploadFile = File(...),
    auto_analyze: bool = Form(default=True),
    model_key: str | None = Form(default=None),
    prompt_version_id: str | None = Form(default=None),
    db: Session = Depends(get_db),
) -> ApiResponse[SessionImportResponseData]:
    extension = Path(file.filename or "").suffix.lower()
    if extension not in ALLOWED_TEXT_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="当前文件类型暂不支持")

    raw_bytes = await file.read()
    raw_text = raw_bytes.decode("utf-8", errors="ignore")
    response = import_text_as_session(
        db,
        raw_text=raw_text,
        title=Path(file.filename or "新对话").stem,
        folder_id=folder_id,
        source_type=SourceType.UPLOAD_FILE,
        original_file_name=file.filename,
        mime_type=file.content_type,
        auto_analyze=auto_analyze,
        model_key=model_key,
        prompt_version_id=prompt_version_id,
    )
    return build_response(response)


@router.get("/sessions/{session_id}/messages", response_model=ApiResponse[SessionMessagesResponseData])
def get_session_messages_route(
    session_id: str,
    db: Session = Depends(get_db),
) -> ApiResponse[SessionMessagesResponseData]:
    return build_response(get_session_messages(db, session_id))


@router.post("/sessions/{session_id}/analyze", response_model=ApiResponse[AnalysisResultData])
def analyze_session_route(
    session_id: str,
    payload: AnalyzeRequest,
    db: Session = Depends(get_db),
) -> ApiResponse[AnalysisResultData]:
    session_obj = get_session_or_404(db, session_id)
    result = create_pending_analysis(
        db,
        session_obj=session_obj,
        model_key=payload.model_key,
        prompt_version_id=payload.prompt_version_id,
        trigger_source=payload.trigger_source,
        module_key=payload.module_key,
    )
    return build_response(result)


@router.get("/sessions/{session_id}/analysis/latest", response_model=ApiResponse[AnalysisResultData])
def get_latest_analysis_route(
    session_id: str,
    module_key: AnalysisModuleKey | None = Query(default=None),
    db: Session = Depends(get_db),
) -> ApiResponse[AnalysisResultData]:
    return build_response(build_analysis_result(db, session_id, module_key=module_key))


@router.get("/prompt-versions", response_model=ApiResponse[PromptVersionListResponseData])
def list_prompt_versions_route(
    tool_key: str | None = Query(default=None),
    task_key: str | None = Query(default=None),
    module_key: AnalysisModuleKey | None = Query(default=None),
    include_content: bool = Query(default=True),
    db: Session = Depends(get_db),
) -> ApiResponse[PromptVersionListResponseData]:
    prompt_config = get_settings().persona_analysis.get_prompt_config(
        module_key or AnalysisModuleKey.USER_PROFILE_AND_REPLY)
    effective_tool_key = tool_key or prompt_config.tool_key
    effective_task_key = task_key or prompt_config.task_key
    items, active_prompt_version_id = list_prompt_versions(
        db, effective_tool_key, effective_task_key)
    if not include_content:
        items = [item.model_copy(update={"content": ""}) for item in items]
    return build_response(
        PromptVersionListResponseData(
            items=items, active_prompt_version_id=active_prompt_version_id)
    )


@router.post("/prompt-versions", response_model=ApiResponse[PromptVersionItemResponseData])
def create_prompt_version_route(
    payload: CreatePromptVersionRequest,
    db: Session = Depends(get_db),
) -> ApiResponse[PromptVersionItemResponseData]:
    prompt_version = create_prompt_version(
        db,
        tool_key=payload.tool_key,
        task_key=payload.task_key,
        version_label=payload.version_label,
        version_note=payload.version_note,
        content=payload.content,
        based_on_prompt_version_id=payload.based_on_prompt_version_id,
        is_active=payload.is_active,
    )
    response_data = PromptVersionItemResponseData(
        item={
            "prompt_version_id": prompt_version.id,
            "tool_key": prompt_version.tool_key,
            "task_key": prompt_version.task_key,
            "version_label": prompt_version.version_label,
            "version_note": prompt_version.version_note,
            "content": prompt_version.content,
            "is_active": prompt_version.is_active,
            "created_at": prompt_version.created_at,
            "updated_at": prompt_version.updated_at,
        }
    )
    return build_response(response_data)


@router.patch("/prompt-versions/{prompt_version_id}", response_model=ApiResponse[PromptVersionItemResponseData])
def update_prompt_version_route(
    prompt_version_id: str,
    payload: UpdatePromptVersionRequest,
    db: Session = Depends(get_db),
) -> ApiResponse[PromptVersionItemResponseData]:
    prompt_version = get_prompt_version_by_id(db, prompt_version_id)
    if prompt_version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="未找到 Prompt 版本")
    updated_version = update_prompt_version(
        db, prompt_version, version_note=payload.version_note, content=payload.content)
    response_data = PromptVersionItemResponseData(
        item={
            "prompt_version_id": updated_version.id,
            "tool_key": updated_version.tool_key,
            "task_key": updated_version.task_key,
            "version_label": updated_version.version_label,
            "version_note": updated_version.version_note,
            "content": updated_version.content,
            "is_active": updated_version.is_active,
            "created_at": updated_version.created_at,
            "updated_at": updated_version.updated_at,
        }
    )
    return build_response(response_data)


@router.post("/prompt-versions/{prompt_version_id}/activate", response_model=ApiResponse[PromptVersionItemResponseData])
def activate_prompt_version_route(
    prompt_version_id: str,
    payload: ActivatePromptVersionRequest,
    db: Session = Depends(get_db),
) -> ApiResponse[PromptVersionItemResponseData]:
    del payload
    prompt_version = get_prompt_version_by_id(db, prompt_version_id)
    if prompt_version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="未找到 Prompt 版本")
    activated_version = activate_prompt_version(db, prompt_version)
    response_data = PromptVersionItemResponseData(
        item={
            "prompt_version_id": activated_version.id,
            "tool_key": activated_version.tool_key,
            "task_key": activated_version.task_key,
            "version_label": activated_version.version_label,
            "version_note": activated_version.version_note,
            "content": activated_version.content,
            "is_active": activated_version.is_active,
            "created_at": activated_version.created_at,
            "updated_at": activated_version.updated_at,
        }
    )
    return build_response(response_data)


@router.get("/model-options", response_model=ApiResponse[ModelOptionsResponseData])
def get_model_options_route() -> ApiResponse[ModelOptionsResponseData]:
    return build_response(ModelOptionsResponseData(items=list_model_options()))
