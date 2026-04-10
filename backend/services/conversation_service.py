from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.db.base import utcnow
from backend.db.models import ConversationFolder, ConversationMessage, ConversationSession, ConversationSource
from backend.domain.enums import AnalysisStatus, ItemType, ParseStatus, SourceType, SpeakerRole, TriggerSource
from backend.parsers.chat_parser import parse_chat_text
from backend.schemas.persona_analysis import (
    ConversationMessageSchema,
    DeleteItemResponseData,
    ItemResponseData,
    RoleSummary,
    SessionImportResponseData,
    SessionMessagesResponseData,
    SidebarItem,
    SidebarResponseData,
)
from backend.services.analysis_service import create_pending_analysis
from backend.services.prompt_service import get_active_prompt_version
from backend.services.model_service import get_default_model_option


def list_sidebar(db: Session) -> SidebarResponseData:
    folders = list(
        db.scalars(
            select(ConversationFolder)
            .options(selectinload(ConversationFolder.sessions))
            .order_by(ConversationFolder.is_pinned.desc(), ConversationFolder.updated_at.desc())
        )
    )
    sessions = list(
        db.scalars(
            select(ConversationSession)
            .order_by(ConversationSession.is_pinned.desc(), ConversationSession.updated_at.desc())
        )
    )

    items = [
        *_folders_to_sidebar_items(folders), *_sessions_to_sidebar_items(sessions)]
    active_session = sessions[0].id if sessions else None
    return SidebarResponseData(items=items, active_session_id=active_session)


def create_folder(db: Session, title: str | None, is_pinned: bool) -> ItemResponseData:
    folder = ConversationFolder(title=title or "新建文件夹", is_pinned=is_pinned)
    db.add(folder)
    db.commit()
    db.refresh(folder)
    return ItemResponseData(item=_folder_to_sidebar_item(folder))


def update_folder(db: Session, folder_id: str, title: str | None, is_pinned: bool | None) -> ItemResponseData:
    folder = db.get(ConversationFolder, folder_id)
    if folder is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="未找到文件夹")
    if title is not None:
        folder.title = title
    if is_pinned is not None:
        folder.is_pinned = is_pinned
    db.add(folder)
    db.commit()
    db.refresh(folder)
    return ItemResponseData(item=_folder_to_sidebar_item(folder))


def create_session(db: Session, title: str | None, folder_id: str | None, is_pinned: bool) -> ItemResponseData:
    if folder_id is not None and db.get(ConversationFolder, folder_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="未找到目标文件夹")
    session_obj = ConversationSession(
        title=title or "新对话",
        folder_id=folder_id,
        is_pinned=is_pinned,
        latest_activity_at=utcnow(),
    )
    db.add(session_obj)
    db.commit()
    db.refresh(session_obj)
    return ItemResponseData(item=_session_to_sidebar_item(session_obj))


def update_session(
    db: Session,
    session_id: str,
    title: str | None,
    is_pinned: bool | None,
    folder_id: str | None,
) -> ItemResponseData:
    session_obj = db.get(ConversationSession, session_id)
    if session_obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="未找到会话")
    if folder_id is not None and db.get(ConversationFolder, folder_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="未找到目标文件夹")
    if title is not None:
        session_obj.title = title
    if is_pinned is not None:
        session_obj.is_pinned = is_pinned
    if folder_id is not None:
        session_obj.folder_id = folder_id
    session_obj.latest_activity_at = utcnow()
    db.add(session_obj)
    db.commit()
    db.refresh(session_obj)
    return ItemResponseData(item=_session_to_sidebar_item(session_obj))


def delete_folder(db: Session, folder_id: str) -> DeleteItemResponseData:
    folder = db.get(ConversationFolder, folder_id)
    if folder is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="未找到文件夹")

    response = DeleteItemResponseData(
        item_id=folder.id,
        item_type=ItemType.FOLDER,
    )
    db.delete(folder)
    db.commit()
    return response


def delete_session(db: Session, session_id: str) -> DeleteItemResponseData:
    session_obj = db.get(ConversationSession, session_id)
    if session_obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="未找到会话")

    response = DeleteItemResponseData(
        item_id=session_obj.id,
        item_type=ItemType.SESSION,
    )
    db.delete(session_obj)
    db.commit()
    return response


def import_text_as_session(
    db: Session,
    *,
    raw_text: str,
    title: str | None,
    folder_id: str | None,
    source_type: SourceType,
    original_file_name: str | None,
    mime_type: str | None,
    auto_analyze: bool,
    model_key: str | None,
    prompt_version_id: str | None,
) -> SessionImportResponseData:
    if folder_id is not None and db.get(ConversationFolder, folder_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="未找到目标文件夹")
    if not raw_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="聊天记录内容不能为空")

    session_obj = ConversationSession(
        title=title or "新对话",
        folder_id=folder_id,
        is_pinned=False,
        parse_status=ParseStatus.PARSING.value,
        analysis_status=AnalysisStatus.PENDING.value,
        latest_activity_at=utcnow(),
    )
    db.add(session_obj)
    db.flush()

    source = ConversationSource(
        session_id=session_obj.id,
        source_type=source_type.value,
        original_file_name=original_file_name,
        mime_type=mime_type,
        raw_text=raw_text,
        parse_status=ParseStatus.PARSING.value,
    )
    db.add(source)
    db.flush()

    parse_result = parse_chat_text(raw_text)
    if not parse_result.messages:
        source.parse_status = ParseStatus.FAILED.value
        source.parse_error = "未能从输入内容中识别有效消息。"
        session_obj.parse_status = ParseStatus.FAILED.value
        db.add_all([source, session_obj])
        db.commit()
        db.refresh(session_obj)
        db.refresh(source)
        return SessionImportResponseData(
            session=_session_to_sidebar_item(session_obj),
            source_id=source.id,
            parse_status=ParseStatus.FAILED,
            message_count=0,
            role_summary=RoleSummary(),
            latest_analysis=None,
        )

    for parsed_message in parse_result.messages:
        db.add(
            ConversationMessage(
                session_id=session_obj.id,
                source_id=source.id,
                message_index=parsed_message.message_index,
                speaker_role=parsed_message.speaker_role.value,
                speaker_name=parsed_message.speaker_name,
                timestamp_text=parsed_message.timestamp_text,
                timestamp_at=parsed_message.timestamp_at,
                content=parsed_message.content,
                raw_content=parsed_message.raw_content,
                parse_note=parsed_message.parse_note,
            )
        )

    source.parse_status = ParseStatus.PARSED.value
    session_obj.parse_status = ParseStatus.PARSED.value
    session_obj.analysis_status = AnalysisStatus.PENDING.value
    session_obj.latest_activity_at = utcnow()
    db.add_all([source, session_obj])
    db.commit()
    db.refresh(session_obj)
    db.refresh(source)

    latest_analysis = None
    if auto_analyze:
        active_prompt_version = prompt_version_id or get_active_prompt_version(
            db).id
        active_model_key = model_key or get_default_model_option().model_key
        latest_analysis = create_pending_analysis(
            db,
            session_obj=session_obj,
            model_key=active_model_key,
            prompt_version_id=active_prompt_version,
            trigger_source=TriggerSource.UPLOAD_AUTO,
        )

    role_summary = RoleSummary(
        teacher_count=parse_result.role_summary.get(SpeakerRole.TEACHER, 0),
        student_count=parse_result.role_summary.get(SpeakerRole.STUDENT, 0),
        unknown_count=parse_result.role_summary.get(SpeakerRole.UNKNOWN, 0),
    )
    return SessionImportResponseData(
        session=_session_to_sidebar_item(session_obj),
        source_id=source.id,
        parse_status=ParseStatus(session_obj.parse_status),
        message_count=len(parse_result.messages),
        role_summary=role_summary,
        latest_analysis=latest_analysis,
    )


def get_session_messages(db: Session, session_id: str) -> SessionMessagesResponseData:
    session_obj = db.scalar(
        select(ConversationSession)
        .options(selectinload(ConversationSession.messages))
        .where(ConversationSession.id == session_id)
    )
    if session_obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="未找到会话")

    messages = [
        ConversationMessageSchema(
            message_id=message.id,
            message_index=message.message_index,
            speaker_role=message.speaker_role,
            speaker_name=message.speaker_name,
            timestamp_text=message.timestamp_text,
            timestamp_at=message.timestamp_at,
            content=message.content,
            raw_content=message.raw_content,
            parse_note=message.parse_note,
        )
        for message in session_obj.messages
    ]

    return SessionMessagesResponseData(
        session_id=session_obj.id,
        title=session_obj.title,
        parse_status=session_obj.parse_status,
        analysis_status=session_obj.analysis_status,
        messages=messages,
    )


def get_session_or_404(db: Session, session_id: str) -> ConversationSession:
    session_obj = db.get(ConversationSession, session_id)
    if session_obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="未找到会话")
    return session_obj


def _folders_to_sidebar_items(folders: list[ConversationFolder]) -> list[SidebarItem]:
    return [_folder_to_sidebar_item(folder) for folder in folders]


def _sessions_to_sidebar_items(sessions: list[ConversationSession]) -> list[SidebarItem]:
    return [_session_to_sidebar_item(session_obj) for session_obj in sessions]


def _folder_to_sidebar_item(folder: ConversationFolder) -> SidebarItem:
    return SidebarItem(
        item_id=folder.id,
        item_type=ItemType.FOLDER,
        title=folder.title,
        is_pinned=folder.is_pinned,
        folder_id=None,
        session_count=len(folder.sessions),
        latest_activity_at=folder.updated_at,
        created_at=folder.created_at,
        updated_at=folder.updated_at,
    )


def _session_to_sidebar_item(session_obj: ConversationSession) -> SidebarItem:
    return SidebarItem(
        item_id=session_obj.id,
        item_type=ItemType.SESSION,
        title=session_obj.title,
        is_pinned=session_obj.is_pinned,
        folder_id=session_obj.folder_id,
        session_count=None,
        latest_activity_at=session_obj.latest_activity_at,
        created_at=session_obj.created_at,
        updated_at=session_obj.updated_at,
    )
