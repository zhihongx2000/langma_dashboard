from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base, TimestampMixin
from backend.domain.enums import AnalysisStatus, ParseStatus, RiskLevel


def generate_id() -> str:
    return str(uuid4())


class ConversationFolder(TimestampMixin, Base):
    __tablename__ = "conversation_folders"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_id)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    is_pinned: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False)

    sessions: Mapped[list[ConversationSession]] = relationship(
        back_populates="folder",
        cascade="all, delete-orphan",
    )


class ConversationSession(TimestampMixin, Base):
    __tablename__ = "conversation_sessions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_id)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    folder_id: Mapped[str | None] = mapped_column(ForeignKey(
        "conversation_folders.id"), nullable=True, index=True)
    is_pinned: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False)
    parse_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=ParseStatus.PENDING.value)
    analysis_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=AnalysisStatus.PENDING.value)
    latest_activity_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True)
    latest_analysis_run_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True)

    folder: Mapped[ConversationFolder | None] = relationship(
        back_populates="sessions")
    sources: Mapped[list[ConversationSource]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
    )
    messages: Mapped[list[ConversationMessage]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ConversationMessage.message_index",
    )
    analysis_runs: Mapped[list[AnalysisRun]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="AnalysisRun.created_at",
    )


class ConversationSource(TimestampMixin, Base):
    __tablename__ = "conversation_sources"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_id)
    session_id: Mapped[str] = mapped_column(ForeignKey(
        "conversation_sessions.id"), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    original_file_name: Mapped[str | None] = mapped_column(
        String(255), nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    parse_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=ParseStatus.PENDING.value)
    parse_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    session: Mapped[ConversationSession] = relationship(
        back_populates="sources")
    messages: Mapped[list[ConversationMessage]
                     ] = relationship(back_populates="source")


class ConversationMessage(TimestampMixin, Base):
    __tablename__ = "conversation_messages"
    __table_args__ = (UniqueConstraint(
        "session_id", "message_index", name="uq_conversation_message_index"),)

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_id)
    session_id: Mapped[str] = mapped_column(ForeignKey(
        "conversation_sessions.id"), nullable=False, index=True)
    source_id: Mapped[str | None] = mapped_column(ForeignKey(
        "conversation_sources.id"), nullable=True, index=True)
    message_index: Mapped[int] = mapped_column(Integer, nullable=False)
    speaker_role: Mapped[str] = mapped_column(String(32), nullable=False)
    speaker_name: Mapped[str | None] = mapped_column(
        String(255), nullable=True)
    timestamp_text: Mapped[str | None] = mapped_column(
        String(255), nullable=True)
    timestamp_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    raw_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    parse_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    session: Mapped[ConversationSession] = relationship(
        back_populates="messages")
    source: Mapped[ConversationSource | None] = relationship(
        back_populates="messages")
    evidences: Mapped[list[FindingEvidence]
                      ] = relationship(back_populates="message")


class PromptVersion(TimestampMixin, Base):
    __tablename__ = "prompt_versions"
    __table_args__ = (
        UniqueConstraint("tool_key", "task_key",
                         "version_label", name="uq_prompt_version"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_id)
    tool_key: Mapped[str] = mapped_column(
        String(128), nullable=False, index=True)
    task_key: Mapped[str] = mapped_column(
        String(128), nullable=False, index=True)
    version_label: Mapped[str] = mapped_column(String(64), nullable=False)
    version_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False)
    based_on_prompt_version_id: Mapped[str | None] = mapped_column(
        ForeignKey("prompt_versions.id"), nullable=True)

    analysis_runs: Mapped[list[AnalysisRun]] = relationship(
        back_populates="prompt_version")


class AnalysisRun(TimestampMixin, Base):
    __tablename__ = "analysis_runs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_id)
    session_id: Mapped[str] = mapped_column(ForeignKey(
        "conversation_sessions.id"), nullable=False, index=True)
    prompt_version_id: Mapped[str | None] = mapped_column(
        ForeignKey("prompt_versions.id"), nullable=True, index=True)
    provider_key: Mapped[str | None] = mapped_column(
        String(128), nullable=True)
    model_key: Mapped[str] = mapped_column(String(128), nullable=False)
    trigger_source: Mapped[str] = mapped_column(String(64), nullable=False)
    module_key: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    analysis_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=AnalysisStatus.PENDING.value)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_level: Mapped[str] = mapped_column(
        String(32), nullable=False, default=RiskLevel.UNKNOWN.value)
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    raw_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    session: Mapped[ConversationSession] = relationship(
        back_populates="analysis_runs")
    prompt_version: Mapped[PromptVersion | None] = relationship(
        back_populates="analysis_runs")
    findings: Mapped[list[AnalysisFinding]] = relationship(
        back_populates="analysis_run",
        cascade="all, delete-orphan",
        order_by="AnalysisFinding.sort_order",
    )


class AnalysisFinding(TimestampMixin, Base):
    __tablename__ = "analysis_findings"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_id)
    analysis_run_id: Mapped[str] = mapped_column(
        ForeignKey("analysis_runs.id"), nullable=False, index=True)
    finding_type: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0)
    severity: Mapped[str | None] = mapped_column(String(32), nullable=True)
    resolution_status: Mapped[str | None] = mapped_column(
        String(64), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    analysis_run: Mapped[AnalysisRun] = relationship(back_populates="findings")
    evidences: Mapped[list[FindingEvidence]] = relationship(
        back_populates="finding",
        cascade="all, delete-orphan",
        order_by="FindingEvidence.created_at",
    )


class FindingEvidence(TimestampMixin, Base):
    __tablename__ = "finding_evidences"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_id)
    finding_id: Mapped[str] = mapped_column(ForeignKey(
        "analysis_findings.id"), nullable=False, index=True)
    message_id: Mapped[str | None] = mapped_column(ForeignKey(
        "conversation_messages.id"), nullable=True, index=True)
    message_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    speaker: Mapped[str | None] = mapped_column(String(255), nullable=True)
    speaker_role: Mapped[str | None] = mapped_column(String(32), nullable=True)
    quote: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp_text: Mapped[str | None] = mapped_column(
        String(255), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    finding: Mapped[AnalysisFinding] = relationship(back_populates="evidences")
    message: Mapped[ConversationMessage | None] = relationship(
        back_populates="evidences")
