from enum import StrEnum


class ItemType(StrEnum):
    FOLDER = "folder"
    SESSION = "session"


class SourceType(StrEnum):
    UPLOAD_FILE = "upload_file"
    PASTED_TEXT = "pasted_text"
    IMPORTED_STRUCTURED_TEXT = "imported_structured_text"


class ParseStatus(StrEnum):
    PENDING = "pending"
    PARSING = "parsing"
    PARSED = "parsed"
    FAILED = "failed"


class SpeakerRole(StrEnum):
    TEACHER = "teacher"
    STUDENT = "student"
    UNKNOWN = "unknown"


class AnalysisStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class FindingType(StrEnum):
    PAIN_POINT = "pain_point"
    DEAL_CLOSING_POINT = "deal_closing_point"
    CHURN_POINT = "churn_point"
    HIGH_FREQUENCY_POINT = "high_frequency_point"
    PERSONA_TAG = "persona_tag"
    RISK_REASON = "risk_reason"
    SMART_REPLY = "smart_reply"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"


class TriggerSource(StrEnum):
    UPLOAD_AUTO = "upload_auto"
    MANUAL_RERUN = "manual_rerun"
    PROMPT_CHANGE = "prompt_change"


class AnalysisModuleKey(StrEnum):
    USER_PROFILE_AND_REPLY = "user_profile_and_reply"
    RISK_DETECTION = "risk_detection"
    FUNNEL_NODES = "funnel_nodes"


class ResolutionStatus(StrEnum):
    UNRESOLVED = "unresolved"
    PARTIALLY_RESOLVED = "partially_resolved"
    RESOLVED = "resolved"


class SeverityLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
