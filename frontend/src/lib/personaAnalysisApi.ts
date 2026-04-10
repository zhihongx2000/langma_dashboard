export interface ApiEnvelope<T> {
    request_id: string;
    data: T;
}

export type ItemType = 'folder' | 'session';
export type SpeakerRole = 'teacher' | 'student' | 'unknown';
export type ParseStatus = 'pending' | 'parsing' | 'parsed' | 'failed';
export type AnalysisStatus = 'pending' | 'running' | 'succeeded' | 'failed';
export type RiskLevel = 'low' | 'medium' | 'high' | 'unknown';
export type TriggerSource = 'upload_auto' | 'manual_rerun' | 'prompt_change';
export type AnalysisModuleKey = 'user_profile_and_reply' | 'risk_detection' | 'funnel_nodes';

export interface SidebarItem {
    item_id: string;
    item_type: ItemType;
    title: string;
    is_pinned: boolean;
    folder_id: string | null;
    session_count: number | null;
    latest_activity_at: string | null;
    created_at: string;
    updated_at: string;
}

export interface SidebarResponseData {
    items: SidebarItem[];
    active_session_id: string | null;
}

export interface ItemResponseData {
    item: SidebarItem;
}

export interface DeleteItemResponseData {
    item_id: string;
    item_type: ItemType;
}

export interface ConversationMessage {
    message_id: string;
    message_index: number;
    speaker_role: SpeakerRole;
    speaker_name: string | null;
    timestamp_text: string | null;
    timestamp_at: string | null;
    content: string;
    raw_content: string | null;
    parse_note: string | null;
}

export interface SessionMessagesResponseData {
    session_id: string;
    title: string;
    parse_status: ParseStatus;
    analysis_status: AnalysisStatus;
    messages: ConversationMessage[];
}

export interface EvidenceItem {
    evidence_id: string;
    message_id: string | null;
    message_index: number | null;
    speaker: string | null;
    speaker_role: SpeakerRole | null;
    quote: string;
    timestamp: string | null;
    note: string | null;
}

export interface FindingItem {
    finding_id: string;
    title: string;
    summary: string;
    reason: string;
    confidence: number;
    severity: string | null;
    resolution_status: string | null;
    evidences: EvidenceItem[];
}

export interface RiskAssessment {
    level: RiskLevel;
    score: number;
    summary: string;
    reason: string;
    evidences: EvidenceItem[];
}

export interface SmartReply {
    reply_id: string;
    style: string;
    content: string;
    reason: string;
    evidences: EvidenceItem[];
}

export interface PromptVersion {
    prompt_version_id: string;
    tool_key: string;
    task_key: string;
    version_label: string;
    version_note: string | null;
    content: string;
    is_active: boolean;
    created_at: string;
    updated_at: string;
}

export interface ModelOption {
    provider_key: string;
    provider_label: string;
    model_key: string;
    model_label: string;
    is_default: boolean;
    is_enabled: boolean;
    temperature: number | null;
    max_tokens: number | null;
}

export interface AnalysisResultData {
    analysis_run_id: string | null;
    session_id: string;
    analysis_status: AnalysisStatus;
    model: ModelOption;
    prompt_version: PromptVersion;
    persona_tags: FindingItem[];
    pain_points: FindingItem[];
    deal_closing_points: FindingItem[];
    churn_points: FindingItem[];
    high_frequency_points: FindingItem[];
    risk_assessment: RiskAssessment;
    smart_replies: SmartReply[];
    summary: string | null;
}

export interface PromptVersionListResponseData {
    items: PromptVersion[];
    active_prompt_version_id: string | null;
}

export interface PromptVersionItemResponseData {
    item: PromptVersion;
}

export interface ModelOptionsResponseData {
    items: ModelOption[];
}

export interface RoleSummary {
    teacher_count: number;
    student_count: number;
    unknown_count: number;
}

export interface SessionImportResponseData {
    session: SidebarItem;
    source_id: string;
    parse_status: ParseStatus;
    message_count: number;
    role_summary: RoleSummary;
    latest_analysis: AnalysisResultData | null;
}

export interface CreateFolderPayload {
    title?: string;
    is_pinned?: boolean;
}

export interface UpdateFolderPayload {
    title?: string;
    is_pinned?: boolean;
}

export interface CreateSessionPayload {
    title?: string;
    folder_id?: string | null;
    is_pinned?: boolean;
}

export interface UpdateSessionPayload {
    title?: string;
    is_pinned?: boolean;
    folder_id?: string | null;
}

export interface ImportTextPayload {
    raw_text: string;
    title?: string;
    folder_id?: string | null;
    source_type?: 'pasted_text' | 'upload_file' | 'imported_structured_text';
    auto_analyze?: boolean;
    model_key?: string;
    prompt_version_id?: string;
}

export interface AnalyzeSessionPayload {
    model_key: string;
    prompt_version_id: string;
    trigger_source: TriggerSource;
    module_key?: AnalysisModuleKey;
}

export interface UpdatePromptVersionPayload {
    version_note?: string | null;
    content?: string;
}

export interface CreatePromptVersionPayload {
    tool_key: string;
    task_key: string;
    version_label: string;
    version_note?: string | null;
    content: string;
    based_on_prompt_version_id?: string | null;
    is_active?: boolean;
}

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, '') ?? '';
const PERSONA_ANALYSIS_PREFIX = '/api/v1/persona-analysis';

function isObject(value: unknown): value is Record<string, unknown> {
    return typeof value === 'object' && value !== null;
}

function buildErrorMessage(status: number, payload: unknown): string {
    if (isObject(payload)) {
        const detail = payload.detail;
        if (typeof detail === 'string' && detail.trim()) {
            return detail;
        }
        if (Array.isArray(detail)) {
            const messages = detail
                .map((item) => (isObject(item) && typeof item.msg === 'string' ? item.msg : null))
                .filter((item): item is string => Boolean(item));
            if (messages.length) {
                return messages.join('；');
            }
        }
        const error = payload.error;
        if (isObject(error) && typeof error.message === 'string' && error.message.trim()) {
            return error.message;
        }
        if (typeof payload.message === 'string' && payload.message.trim()) {
            return payload.message;
        }
    }
    return `请求失败（${status}）`;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
    const headers = new Headers(init?.headers);
    const isFormData = typeof FormData !== 'undefined' && init?.body instanceof FormData;

    if (init?.body && !isFormData && !headers.has('Content-Type')) {
        headers.set('Content-Type', 'application/json');
    }

    const response = await fetch(`${API_BASE_URL}${PERSONA_ANALYSIS_PREFIX}${path}`, {
        ...init,
        headers,
    });

    const rawText = await response.text();
    const payload = rawText ? (JSON.parse(rawText) as ApiEnvelope<T> | Record<string, unknown>) : null;

    if (!response.ok) {
        throw new Error(buildErrorMessage(response.status, payload));
    }

    if (!payload || !isObject(payload) || !('data' in payload)) {
        throw new Error('接口返回格式不正确');
    }

    return payload.data as T;
}

export function getSidebar(): Promise<SidebarResponseData> {
    return request<SidebarResponseData>('/sidebar');
}

export function createFolder(payload: CreateFolderPayload): Promise<ItemResponseData> {
    return request<ItemResponseData>('/folders', {
        method: 'POST',
        body: JSON.stringify(payload),
    });
}

export function updateFolder(folderId: string, payload: UpdateFolderPayload): Promise<ItemResponseData> {
    return request<ItemResponseData>(`/folders/${folderId}`, {
        method: 'PATCH',
        body: JSON.stringify(payload),
    });
}

export function deleteFolder(folderId: string): Promise<DeleteItemResponseData> {
    return request<DeleteItemResponseData>(`/folders/${folderId}`, {
        method: 'DELETE',
    });
}

export function createSession(payload: CreateSessionPayload): Promise<ItemResponseData> {
    return request<ItemResponseData>('/sessions', {
        method: 'POST',
        body: JSON.stringify(payload),
    });
}

export function updateSession(sessionId: string, payload: UpdateSessionPayload): Promise<ItemResponseData> {
    return request<ItemResponseData>(`/sessions/${sessionId}`, {
        method: 'PATCH',
        body: JSON.stringify(payload),
    });
}

export function deleteSession(sessionId: string): Promise<DeleteItemResponseData> {
    return request<DeleteItemResponseData>(`/sessions/${sessionId}`, {
        method: 'DELETE',
    });
}

export function importTextSession(payload: ImportTextPayload): Promise<SessionImportResponseData> {
    return request<SessionImportResponseData>('/sessions/import-text', {
        method: 'POST',
        body: JSON.stringify(payload),
    });
}

export function uploadChatRecord(
    folderId: string,
    file: File,
    options: {
        autoAnalyze?: boolean;
        modelKey?: string;
        promptVersionId?: string;
    },
): Promise<SessionImportResponseData> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('auto_analyze', String(options.autoAnalyze ?? true));

    if (options.modelKey) {
        formData.append('model_key', options.modelKey);
    }
    if (options.promptVersionId) {
        formData.append('prompt_version_id', options.promptVersionId);
    }

    return request<SessionImportResponseData>(`/folders/${folderId}/uploads`, {
        method: 'POST',
        body: formData,
    });
}

export function getSessionMessages(sessionId: string): Promise<SessionMessagesResponseData> {
    return request<SessionMessagesResponseData>(`/sessions/${sessionId}/messages`);
}

export function analyzeSession(sessionId: string, payload: AnalyzeSessionPayload): Promise<AnalysisResultData> {
    return request<AnalysisResultData>(`/sessions/${sessionId}/analyze`, {
        method: 'POST',
        body: JSON.stringify(payload),
    });
}

export function getLatestAnalysis(sessionId: string, moduleKey?: AnalysisModuleKey): Promise<AnalysisResultData> {
    const query = moduleKey ? `?module_key=${moduleKey}` : '';
    return request<AnalysisResultData>(`/sessions/${sessionId}/analysis/latest${query}`);
}

export function getModelOptions(): Promise<ModelOptionsResponseData> {
    return request<ModelOptionsResponseData>('/model-options');
}

export function listPromptVersions(
    toolKey = 'user_profiling_analysis',
    taskKey = 'analyze_chat',
    moduleKey?: AnalysisModuleKey,
): Promise<PromptVersionListResponseData> {
    const query = new URLSearchParams({ include_content: 'true' });
    query.set('tool_key', toolKey);
    if (taskKey) {
        query.set('task_key', taskKey);
    }
    if (moduleKey) {
        query.set('module_key', moduleKey);
    }
    return request<PromptVersionListResponseData>(`/prompt-versions?${query.toString()}`);
}

export function updatePromptVersion(
    promptVersionId: string,
    payload: UpdatePromptVersionPayload,
): Promise<PromptVersionItemResponseData> {
    return request<PromptVersionItemResponseData>(`/prompt-versions/${promptVersionId}`, {
        method: 'PATCH',
        body: JSON.stringify(payload),
    });
}

export function createPromptVersion(payload: CreatePromptVersionPayload): Promise<PromptVersionItemResponseData> {
    return request<PromptVersionItemResponseData>('/prompt-versions', {
        method: 'POST',
        body: JSON.stringify(payload),
    });
}

export function activatePromptVersion(promptVersionId: string): Promise<PromptVersionItemResponseData> {
    return request<PromptVersionItemResponseData>(`/prompt-versions/${promptVersionId}/activate`, {
        method: 'POST',
        body: JSON.stringify({ activation_note: null }),
    });
}