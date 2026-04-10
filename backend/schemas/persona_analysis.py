from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from backend.domain.enums import (
    AnalysisModuleKey,
    AnalysisStatus,
    ItemType,
    ParseStatus,
    ResolutionStatus,
    RiskLevel,
    SeverityLevel,
    SourceType,
    SpeakerRole,
    TriggerSource,
)


class SchemaBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class SidebarItem(SchemaBase):
    item_id: str
    item_type: ItemType
    title: str
    is_pinned: bool
    folder_id: str | None = None
    session_count: int | None = None
    latest_activity_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ConversationMessageSchema(SchemaBase):
    message_id: str
    message_index: int
    speaker_role: SpeakerRole
    speaker_name: str | None = None
    timestamp_text: str | None = None
    timestamp_at: datetime | None = None
    content: str
    raw_content: str | None = None
    parse_note: str | None = None


class EvidenceItem(SchemaBase):
    evidence_id: str
    message_id: str | None = None
    message_index: int | None = None
    speaker: str | None = None
    speaker_role: SpeakerRole | None = None
    quote: str
    timestamp: str | None = None
    note: str | None = None


class FindingItem(SchemaBase):
    finding_id: str
    title: str
    summary: str
    reason: str
    confidence: float
    severity: SeverityLevel | None = None
    resolution_status: ResolutionStatus | None = None
    evidences: list[EvidenceItem] = Field(default_factory=list)


class RiskAssessment(SchemaBase):
    level: RiskLevel
    score: int
    summary: str
    reason: str
    evidences: list[EvidenceItem] = Field(default_factory=list)


class SmartReply(SchemaBase):
    reply_id: str
    style: str
    content: str
    reason: str
    evidences: list[EvidenceItem] = Field(default_factory=list)


class PromptVersionSchema(SchemaBase):
    prompt_version_id: str
    tool_key: str
    task_key: str
    version_label: str
    version_note: str | None = None
    content: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ModelOptionSchema(SchemaBase):
    provider_key: str
    provider_label: str
    model_key: str
    model_label: str
    is_default: bool
    is_enabled: bool
    temperature: float | None = None
    max_tokens: int | None = None


class RoleSummary(SchemaBase):
    teacher_count: int = 0
    student_count: int = 0
    unknown_count: int = 0


class SidebarResponseData(SchemaBase):
    items: list[SidebarItem]
    active_session_id: str | None = None


class ItemResponseData(SchemaBase):
    item: SidebarItem


class DeleteItemResponseData(SchemaBase):
    item_id: str
    item_type: ItemType


class SessionImportResponseData(SchemaBase):
    session: SidebarItem
    source_id: str
    parse_status: ParseStatus
    message_count: int
    role_summary: RoleSummary
    latest_analysis: AnalysisResultData | None = None


class SessionMessagesResponseData(SchemaBase):
    session_id: str
    title: str
    parse_status: ParseStatus
    analysis_status: AnalysisStatus
    messages: list[ConversationMessageSchema]


class PromptVersionListResponseData(SchemaBase):
    items: list[PromptVersionSchema]
    active_prompt_version_id: str | None = None


class PromptVersionItemResponseData(SchemaBase):
    item: PromptVersionSchema


class ModelOptionsResponseData(SchemaBase):
    items: list[ModelOptionSchema]


class AnalysisResultData(SchemaBase):
    analysis_run_id: str | None = None
    session_id: str
    analysis_status: AnalysisStatus
    model: ModelOptionSchema
    prompt_version: PromptVersionSchema
    persona_tags: list[FindingItem] = Field(default_factory=list)
    pain_points: list[FindingItem] = Field(default_factory=list)
    deal_closing_points: list[FindingItem] = Field(default_factory=list)
    churn_points: list[FindingItem] = Field(default_factory=list)
    high_frequency_points: list[FindingItem] = Field(default_factory=list)
    risk_assessment: RiskAssessment
    smart_replies: list[SmartReply] = Field(default_factory=list)
    summary: str | None = None


class CreateFolderRequest(BaseModel):
    title: str | None = None
    is_pinned: bool = False


class UpdateFolderRequest(BaseModel):
    title: str | None = None
    is_pinned: bool | None = None


class CreateSessionRequest(BaseModel):
    title: str | None = None
    folder_id: str | None = None
    is_pinned: bool = False


class UpdateSessionRequest(BaseModel):
    title: str | None = None
    is_pinned: bool | None = None
    folder_id: str | None = None


class ImportTextRequest(BaseModel):
    raw_text: str
    title: str | None = None
    folder_id: str | None = None
    source_type: SourceType = SourceType.PASTED_TEXT
    auto_analyze: bool = True
    model_key: str | None = None
    prompt_version_id: str | None = None


class AnalyzeRequest(BaseModel):
    model_key: str
    prompt_version_id: str
    trigger_source: TriggerSource = TriggerSource.MANUAL_RERUN
    module_key: AnalysisModuleKey = AnalysisModuleKey.USER_PROFILE_AND_REPLY


class CreatePromptVersionRequest(BaseModel):
    tool_key: str
    task_key: str
    version_label: str
    version_note: str | None = None
    content: str
    based_on_prompt_version_id: str | None = None
    is_active: bool = False


class UpdatePromptVersionRequest(BaseModel):
    version_note: str | None = None
    content: str | None = None


class ActivatePromptVersionRequest(BaseModel):
    activation_note: str | None = None


class StructuredEvidenceInput(BaseModel):
    message_index: int | None = None
    speaker: str | None = None
    speaker_role: SpeakerRole | None = None
    timestamp: str | None = None
    quote: str
    note: str | None = None


class StructuredFindingInput(BaseModel):
    title: str
    summary: str
    reason: str
    confidence: float
    severity: SeverityLevel | None = None
    resolution_status: ResolutionStatus | None = None
    evidences: list[StructuredEvidenceInput] = Field(default_factory=list)


class StructuredRiskAssessmentInput(BaseModel):
    level: RiskLevel
    score: int
    summary: str
    reason: str
    evidences: list[StructuredEvidenceInput] = Field(default_factory=list)


class StructuredSmartReplyInput(BaseModel):
    style: str
    content: str
    reason: str
    evidences: list[StructuredEvidenceInput] = Field(default_factory=list)


class StructuredAnalysisOutput(BaseModel):
    session_id: str
    conversation_summary: str
    parser_notes: list[str] = Field(default_factory=list)
    persona_tags: list[StructuredFindingInput] = Field(default_factory=list)
    pain_points: list[StructuredFindingInput] = Field(default_factory=list)
    deal_closing_points: list[StructuredFindingInput] = Field(
        default_factory=list)
    churn_points: list[StructuredFindingInput] = Field(default_factory=list)
    high_frequency_points: list[StructuredFindingInput] = Field(
        default_factory=list)
    risk_assessment: StructuredRiskAssessmentInput
    smart_replies: list[StructuredSmartReplyInput] = Field(
        default_factory=list)
