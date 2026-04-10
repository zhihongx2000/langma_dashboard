import {
  ArrowLeft,
  BarChart2,
  ChevronDown,
  ChevronRight,
  FileText,
  Folder,
  FolderOpen,
  FolderPlus,
  History,
  LoaderCircle,
  Pin,
  Plus,
  Save,
  Settings,
  Trash2,
  Upload,
  X,
  Zap,
} from 'lucide-react';
import { type ChangeEvent, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  activatePromptVersion,
  analyzeSession,
  createPromptVersion,
  createFolder,
  deleteFolder,
  deleteSession,
  getLatestAnalysis,
  getModelOptions,
  getSessionMessages,
  getSidebar,
  importTextSession,
  listPromptVersions,
  updateFolder,
  updateSession,
  uploadChatRecord,
  type AnalysisModuleKey,
  type AnalysisResultData,
  type AnalysisStatus,
  type ConversationMessage,
  type EvidenceItem,
  type FindingItem,
  type ModelOption,
  type ParseStatus,
  type PromptVersion,
  type SidebarItem,
  type SmartReply,
  type TriggerSource,
} from '../lib/personaAnalysisApi';

const TOOL_KEY = 'user_profiling_analysis';
const MODULE_TASK_MAP: Record<AnalysisModuleKey, string> = {
  user_profile_and_reply: 'user_profile_and_reply',
  risk_detection: 'risk_detection',
  funnel_nodes: 'funnel_nodes',
};
const MODULE_OPTIONS: Array<{ key: AnalysisModuleKey; label: string }> = [
  { key: 'user_profile_and_reply', label: '用户标签 + 推荐话术' },
  { key: 'risk_detection', label: '高风险学员识别' },
  { key: 'funnel_nodes', label: '痛点/成交/流失/高频节点' },
];
function getModuleLabel(moduleKey: AnalysisModuleKey): string {
  return MODULE_OPTIONS.find((item) => item.key === moduleKey)?.label ?? moduleKey;
}
const SUPPORTED_UPLOAD_ACCEPT = '.txt,.csv,.json,.md,.log';

type ContextMenuState =
  | {
    x: number;
    y: number;
    type: 'empty';
  }
  | {
    x: number;
    y: number;
    type: 'item';
    item: SidebarItem;
  };

type NoticeState = {
  type: 'success' | 'error';
  text: string;
} | null;

type SessionViewState = {
  title: string;
  parseStatus: ParseStatus;
  analysisStatus: AnalysisStatus;
  messages: ConversationMessage[];
};

type ModulePromptDraft = {
  selectedPromptVersionId: string;
  currentPromptText: string;
};

const EMPTY_SESSION_STATE: SessionViewState = {
  title: '',
  parseStatus: 'pending',
  analysisStatus: 'pending',
  messages: [],
};

const EMPTY_RISK_ASSESSMENT: AnalysisResultData['risk_assessment'] = {
  level: 'unknown',
  score: 0,
  summary: '正在执行分析。',
  reason: '模型正在处理本次会话，请稍候。',
  evidences: [],
};

function sortSidebarItems(items: SidebarItem[]): SidebarItem[] {
  return [...items].sort((left, right) => {
    if (left.is_pinned !== right.is_pinned) {
      return left.is_pinned ? -1 : 1;
    }
    if (left.item_type !== right.item_type) {
      return left.item_type === 'folder' ? -1 : 1;
    }
    const leftTime = new Date(left.latest_activity_at ?? left.updated_at).getTime();
    const rightTime = new Date(right.latest_activity_at ?? right.updated_at).getTime();
    return rightTime - leftTime;
  });
}

function getErrorMessage(error: unknown): string {
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return '请求执行失败，请稍后重试。';
}

function getSpeakerAppearance(role: ConversationMessage['speaker_role'] | EvidenceItem['speaker_role']) {
  if (role === 'student') {
    return {
      bubble: 'bg-secondary-container text-on-secondary-container rounded-tl-sm',
      badge: 'bg-secondary text-white',
      name: 'text-on-surface',
      align: 'items-start',
      reverse: '',
      label: '生',
    };
  }

  if (role === 'teacher') {
    return {
      bubble: 'bg-primary text-on-primary rounded-tr-sm',
      badge: 'bg-primary text-white',
      name: 'text-primary',
      align: 'items-end ml-auto',
      reverse: 'flex-row-reverse',
      label: '师',
    };
  }

  return {
    bubble: 'bg-surface-container text-on-surface rounded-2xl',
    badge: 'bg-outline text-white',
    name: 'text-on-surface-variant',
    align: 'items-start',
    reverse: '',
    label: '未',
  };
}

function getParseStatusLabel(status: ParseStatus): string {
  switch (status) {
    case 'parsing':
      return '解析中';
    case 'parsed':
      return '已解析';
    case 'failed':
      return '解析失败';
    default:
      return '待解析';
  }
}

function getAnalysisStatusLabel(status: AnalysisStatus): string {
  switch (status) {
    case 'running':
      return '分析中';
    case 'succeeded':
      return '分析完成';
    case 'failed':
      return '分析失败';
    default:
      return '待分析';
  }
}

function getRiskPresentation(level: AnalysisResultData['risk_assessment']['level']) {
  switch (level) {
    case 'high':
      return {
        label: '高',
        panel: 'bg-[#ffdad6]/50 border border-[#ba1a1a]/10',
        text: 'text-[#ba1a1a]',
        softText: 'text-[#93000a]',
        bar: 'bg-[#ba1a1a]',
      };
    case 'medium':
      return {
        label: '中',
        panel: 'bg-[#fff1c7]/60 border border-[#785900]/10',
        text: 'text-[#785900]',
        softText: 'text-[#5d4300]',
        bar: 'bg-[#b88900]',
      };
    case 'low':
      return {
        label: '低',
        panel: 'bg-[#d9f8d6]/60 border border-[#0c5216]/10',
        text: 'text-[#0c5216]',
        softText: 'text-[#164b1d]',
        bar: 'bg-[#0c5216]',
      };
    default:
      return {
        label: '未知',
        panel: 'bg-surface-container border border-outline-variant/10',
        text: 'text-on-surface',
        softText: 'text-on-surface-variant',
        bar: 'bg-outline',
      };
  }
}

function formatMessageTime(message: ConversationMessage): string {
  if (message.timestamp_text) {
    return message.timestamp_text;
  }
  if (!message.timestamp_at) {
    return '未标记时间';
  }
  return new Date(message.timestamp_at).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function stripFileExtension(fileName: string): string {
  return fileName.replace(/\.[^/.]+$/, '');
}

function readFileAsText(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result ?? ''));
    reader.onerror = () => reject(new Error('文件读取失败，请更换文件后重试。'));
    reader.readAsText(file, 'utf-8');
  });
}

function generateNextVersionLabel(versions: PromptVersion[]): string {
  const usedNumbers = versions
    .map((item) => {
      const match = item.version_label.match(/^v(\d+)$/i);
      return match ? Number.parseInt(match[1], 10) : null;
    })
    .filter((value): value is number => value !== null && Number.isFinite(value));

  const nextNumber = usedNumbers.length ? Math.max(...usedNumbers) + 1 : versions.length + 1;
  return `v${nextNumber}`;
}

function getConciseFindingTitle(title: string, summary: string): string {
  const normalizedTitle = title.trim();
  const normalizedSummary = summary.trim();
  const shouldUseSummary =
    !normalizedTitle
    || normalizedTitle.length > 20
    || normalizedTitle === normalizedSummary
    || normalizedSummary.startsWith(normalizedTitle)
    || normalizedTitle.startsWith(normalizedSummary);

  let candidate = shouldUseSummary ? normalizedSummary : normalizedTitle;
  candidate = candidate.split(/[，。；,.!?！？]/)[0]?.trim() ?? '';

  if (!candidate) {
    return '未命名要点';
  }
  return candidate.length > 18 ? `${candidate.slice(0, 18)}...` : candidate;
}

function EvidenceList({ evidences }: { evidences: EvidenceItem[] }) {
  if (!evidences.length) {
    return null;
  }

  return (
    <div className="mt-3 flex flex-col gap-2">
      {evidences.slice(0, 2).map((evidence) => (
        <div key={evidence.evidence_id} className="rounded-xl border border-outline-variant/10 bg-surface px-3 py-3">
          <p className="text-xs leading-relaxed text-on-surface">“{evidence.quote}”</p>
          <p className="mt-2 text-[10px] font-medium text-outline">
            {[evidence.speaker, evidence.timestamp, evidence.note].filter(Boolean).join(' · ') || '证据已关联'}
          </p>
        </div>
      ))}
      {evidences.length > 2 && (
        <p className="text-[10px] font-medium text-outline">还有 {evidences.length - 2} 条证据未展开</p>
      )}
    </div>
  );
}

function FindingSection({
  title,
  emptyText,
  accentClass,
  items,
}: {
  title: string;
  emptyText: string;
  accentClass: string;
  items: FindingItem[];
}) {
  return (
    <div className={`bg-surface-container-lowest p-5 rounded-xl shadow-sm border-l-4 ${accentClass}`}>
      <p className="text-[10px] font-bold mb-3 uppercase tracking-tighter text-outline">{title}</p>
      {items.length ? (
        <div className="space-y-4">
          {items.map((item) => (
            <div key={item.finding_id} className="rounded-xl bg-surface px-4 py-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-sm font-bold text-on-surface">{getConciseFindingTitle(item.title, item.summary)}</p>
                  <p className="mt-1 text-sm leading-relaxed text-on-surface-variant">{item.summary}</p>
                </div>
                <span className="shrink-0 rounded-full bg-surface-container px-2 py-1 text-[10px] font-bold text-outline">
                  {Math.round(item.confidence * 100)}%
                </span>
              </div>
              <p className="mt-3 text-xs leading-relaxed text-outline">判断理由：{item.reason}</p>
              <EvidenceList evidences={item.evidences} />
            </div>
          ))}
        </div>
      ) : (
        <p className="text-sm leading-relaxed text-outline">{emptyText}</p>
      )}
    </div>
  );
}

function SmartReplySection({ replies, onCopy }: { replies: SmartReply[]; onCopy: (content: string) => void }) {
  if (!replies.length) {
    return (
      <div className="bg-primary p-5 rounded-xl shadow-lg">
        <p className="text-[10px] font-bold text-[#afefdd] mb-3 uppercase tracking-tighter">推荐话术</p>
        <p className="text-sm leading-relaxed text-[#d6f5ea]">当前分析结果尚未生成推荐话术。</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      {replies.map((reply) => (
        <div key={reply.reply_id} className="bg-primary p-5 rounded-xl shadow-lg">
          <div className="flex items-center justify-between gap-3">
            <p className="text-[10px] font-bold text-[#afefdd] uppercase tracking-tighter">推荐话术 · {reply.style}</p>
            <button
              onClick={() => onCopy(reply.content)}
              className="rounded-lg bg-[#afefdd] px-3 py-1.5 text-[10px] font-bold text-[#00201a] hover:opacity-90 transition-opacity"
            >
              复制话术
            </button>
          </div>
          <p className="mt-4 text-sm italic leading-relaxed text-[#d6f5ea]">“{reply.content}”</p>
          <p className="mt-4 text-xs leading-relaxed text-[#7ebdac]">生成理由：{reply.reason}</p>
          <EvidenceList evidences={reply.evidences} />
        </div>
      ))}
    </div>
  );
}

export default function PersonaAnalysis() {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const activeSessionIdRef = useRef<string | null>(null);

  const [isConfigModalOpen, setIsConfigModalOpen] = useState(false);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [contextMenu, setContextMenu] = useState<ContextMenuState | null>(null);
  const [editingItemId, setEditingItemId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState('');
  const [sidebarItems, setSidebarItems] = useState<SidebarItem[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [sessionView, setSessionView] = useState<SessionViewState>(EMPTY_SESSION_STATE);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResultData | null>(null);
  const [modelOptions, setModelOptions] = useState<ModelOption[]>([]);
  const [promptVersions, setPromptVersions] = useState<PromptVersion[]>([]);
  const [selectedModuleKey, setSelectedModuleKey] = useState<AnalysisModuleKey>('user_profile_and_reply');
  const [moduleModelKeys, setModuleModelKeys] = useState<Record<AnalysisModuleKey, string>>({
    user_profile_and_reply: '',
    risk_detection: '',
    funnel_nodes: '',
  });
  const [modulePromptDrafts, setModulePromptDrafts] = useState<Record<AnalysisModuleKey, ModulePromptDraft>>({
    user_profile_and_reply: { selectedPromptVersionId: '', currentPromptText: '' },
    risk_detection: { selectedPromptVersionId: '', currentPromptText: '' },
    funnel_nodes: { selectedPromptVersionId: '', currentPromptText: '' },
  });
  const [enabledModules, setEnabledModules] = useState<Set<AnalysisModuleKey>>(
    () => new Set<AnalysisModuleKey>(['user_profile_and_reply', 'risk_detection', 'funnel_nodes']),
  );
  const [moduleResults, setModuleResults] = useState<Record<AnalysisModuleKey, AnalysisResultData | null>>({
    user_profile_and_reply: null,
    risk_detection: null,
    funnel_nodes: null,
  });
  const [activeResultTab, setActiveResultTab] = useState<AnalysisModuleKey>('user_profile_and_reply');
  const [selectedModelKey, setSelectedModelKey] = useState('');
  const [selectedPromptVersionId, setSelectedPromptVersionId] = useState('');
  const [activePromptVersionId, setActivePromptVersionId] = useState<string | null>(null);
  const [currentPromptText, setCurrentPromptText] = useState('');
  const [selectedUploadFolderId, setSelectedUploadFolderId] = useState<string | null>(null);
  const [uploadReplaceSessionId, setUploadReplaceSessionId] = useState<string | null>(null);
  const [isInitialLoading, setIsInitialLoading] = useState(true);
  const [isSessionLoading, setIsSessionLoading] = useState(false);
  const [isSidebarRefreshing, setIsSidebarRefreshing] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isRunningAnalysis, setIsRunningAnalysis] = useState(false);
  const [isAnalysisPolling, setIsAnalysisPolling] = useState(false);
  const [expandedFolderIds, setExpandedFolderIds] = useState<Set<string>>(() => new Set());
  const [isSavingPrompt, setIsSavingPrompt] = useState(false);
  const [draggingSessionId, setDraggingSessionId] = useState<string | null>(null);
  const [dragOverFolderId, setDragOverFolderId] = useState<string | null>(null);
  const [notice, setNotice] = useState<NoticeState>(null);

  useEffect(() => {
    const handleClickOutside = () => setContextMenu(null);
    window.addEventListener('click', handleClickOutside);
    return () => window.removeEventListener('click', handleClickOutside);
  }, []);

  useEffect(() => {
    activeSessionIdRef.current = activeSessionId;
  }, [activeSessionId]);

  // 当活跃会话变化时，自动展开其所属文件夹
  useEffect(() => {
    if (!activeSessionId) {
      return;
    }
    const session = sidebarItems.find((item) => item.item_id === activeSessionId);
    if (session?.folder_id) {
      setExpandedFolderIds((prev) => {
        if (prev.has(session.folder_id!)) {
          return prev;
        }
        return new Set([...prev, session.folder_id!]);
      });
    }
  }, [activeSessionId, sidebarItems]);

  useEffect(() => {
    if (!notice) {
      return undefined;
    }

    const timer = window.setTimeout(() => setNotice(null), 5000);
    return () => window.clearTimeout(timer);
  }, [notice]);

  useEffect(() => {
    let cancelled = false;

    async function loadInitialData() {
      setIsInitialLoading(true);
      try {
        const [sidebarData, modelData] = await Promise.all([
          getSidebar(),
          getModelOptions(),
        ]);

        if (cancelled) {
          return;
        }

        const sortedItems = sortSidebarItems(sidebarData.items);
        setSidebarItems(sortedItems);

        setModelOptions(modelData.items);
        const defaultModelKey = modelData.items.find((item) => item.is_default)?.model_key ?? modelData.items[0]?.model_key ?? '';
        setSelectedModelKey(defaultModelKey);
        setModuleModelKeys({
          user_profile_and_reply: defaultModelKey,
          risk_detection: defaultModelKey,
          funnel_nodes: defaultModelKey,
        });

        const nextSessionId = sidebarData.active_session_id ?? sortedItems.find((item) => item.item_type === 'session')?.item_id ?? null;
        setActiveSessionId(nextSessionId);
      } catch (error) {
        setNotice({ type: 'error', text: getErrorMessage(error) });
      } finally {
        if (!cancelled) {
          setIsInitialLoading(false);
        }
      }
    }

    loadInitialData();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function loadPromptVersionsForModule() {
      try {
        const promptData = await listPromptVersions(TOOL_KEY, MODULE_TASK_MAP[selectedModuleKey], selectedModuleKey);
        if (cancelled) {
          return;
        }
        const draft = modulePromptDrafts[selectedModuleKey];
        const draftPromptExists = draft.selectedPromptVersionId
          ? promptData.items.some((item) => item.prompt_version_id === draft.selectedPromptVersionId)
          : false;

        const nextPromptId =
          draftPromptExists
            ? draft.selectedPromptVersionId
            : promptData.active_prompt_version_id ?? promptData.items[0]?.prompt_version_id ?? '';
        const fallbackContent = promptData.items.find((item) => item.prompt_version_id === nextPromptId)?.content ?? '';
        const nextPromptText = draftPromptExists && draft.currentPromptText ? draft.currentPromptText : fallbackContent;

        setPromptVersions(promptData.items);
        setActivePromptVersionId(promptData.active_prompt_version_id);
        setSelectedPromptVersionId(nextPromptId);
        setCurrentPromptText(nextPromptText);
        setSelectedModelKey(moduleModelKeys[selectedModuleKey] || selectedModelKey);
        setModulePromptDrafts((current) => ({
          ...current,
          [selectedModuleKey]: {
            selectedPromptVersionId: nextPromptId,
            currentPromptText: nextPromptText,
          },
        }));
      } catch (error) {
        if (!cancelled) {
          setNotice({ type: 'error', text: getErrorMessage(error) });
        }
      }
    }

    void loadPromptVersionsForModule();
    return () => {
      cancelled = true;
    };
  }, [selectedModuleKey]);

  function upsertSidebarItem(nextItem: SidebarItem) {
    setSidebarItems((current) => {
      const nextItems = current.filter((item) => item.item_id !== nextItem.item_id);
      nextItems.unshift(nextItem);
      return sortSidebarItems(nextItems);
    });
  }

  function buildPendingAnalysisResult(sessionId: string): AnalysisResultData | null {
    const currentSessionAnalysis = analysisResult?.session_id === sessionId ? analysisResult : null;
    const model = modelOptions.find((item) => item.model_key === selectedModelKey) ?? currentSessionAnalysis?.model;
    const promptVersion = promptVersions.find((item) => item.prompt_version_id === selectedPromptVersionId) ?? currentSessionAnalysis?.prompt_version;

    if (!model || !promptVersion) {
      return currentSessionAnalysis;
    }

    return {
      analysis_run_id: currentSessionAnalysis?.analysis_run_id ?? null,
      session_id: sessionId,
      analysis_status: 'running',
      model,
      prompt_version: promptVersion,
      persona_tags: currentSessionAnalysis?.persona_tags ?? [],
      pain_points: currentSessionAnalysis?.pain_points ?? [],
      deal_closing_points: currentSessionAnalysis?.deal_closing_points ?? [],
      churn_points: currentSessionAnalysis?.churn_points ?? [],
      high_frequency_points: currentSessionAnalysis?.high_frequency_points ?? [],
      risk_assessment: currentSessionAnalysis?.risk_assessment ?? EMPTY_RISK_ASSESSMENT,
      smart_replies: currentSessionAnalysis?.smart_replies ?? [],
      summary: '正在执行分析。',
    };
  }

  async function loadSessionMessages(sessionId: string, showLoading = true) {
    if (showLoading) {
      setIsSessionLoading(true);
    }

    try {
      const messagesData = await getSessionMessages(sessionId);
      if (activeSessionIdRef.current !== sessionId) {
        return messagesData;
      }

      setSessionView({
        title: messagesData.title,
        parseStatus: messagesData.parse_status,
        analysisStatus: messagesData.analysis_status,
        messages: [...messagesData.messages].sort((left, right) => left.message_index - right.message_index),
      });
      return messagesData;
    } finally {
      if (showLoading && activeSessionIdRef.current === sessionId) {
        setIsSessionLoading(false);
      }
    }
  }

  async function loadLatestAnalysis(sessionId: string) {
    const [r1, r2, r3] = await Promise.allSettled([
      getLatestAnalysis(sessionId, 'user_profile_and_reply'),
      getLatestAnalysis(sessionId, 'risk_detection'),
      getLatestAnalysis(sessionId, 'funnel_nodes'),
    ]);
    const results: Record<AnalysisModuleKey, AnalysisResultData | null> = {
      user_profile_and_reply: r1.status === 'fulfilled' ? r1.value : null,
      risk_detection: r2.status === 'fulfilled' ? r2.value : null,
      funnel_nodes: r3.status === 'fulfilled' ? r3.value : null,
    };
    if (activeSessionIdRef.current === sessionId) {
      setModuleResults(results);
      // Keep legacy analysisResult pointing to the active tab's result for backward compat with status indicators
      setAnalysisResult(results[activeResultTab] ?? null);
      const anyRunning = Object.values(results).some((r) => r?.analysis_status === 'running');
      const anySucceeded = Object.values(results).some((r) => r?.analysis_status === 'succeeded');
      const overallStatus: AnalysisStatus = anyRunning
        ? 'running'
        : anySucceeded
          ? 'succeeded'
          : (results.user_profile_and_reply?.analysis_status ?? 'pending');
      setSessionView((current) => ({ ...current, analysisStatus: overallStatus }));
      if (!anyRunning) {
        setIsAnalysisPolling(false);
      }
    }
    return results;
  }

  useEffect(() => {
    if (!activeSessionId) {
      setSessionView(EMPTY_SESSION_STATE);
      setModuleResults({ user_profile_and_reply: null, risk_detection: null, funnel_nodes: null });
      setAnalysisResult(null);
      setIsAnalysisPolling(false);
      return;
    }

    let cancelled = false;
    setIsSessionLoading(true);

    Promise.all([loadSessionMessages(activeSessionId, false), loadLatestAnalysis(activeSessionId)])
      .then(([, resultsData]) => {
        if (cancelled) {
          return;
        }
        const anyRunning = Object.values(resultsData).some((r) => r?.analysis_status === 'running');
        if (!anyRunning) {
          setIsAnalysisPolling(false);
        }
      })
      .catch((error) => {
        if (!cancelled) {
          setNotice({ type: 'error', text: getErrorMessage(error) });
          setSessionView(EMPTY_SESSION_STATE);
          setModuleResults({ user_profile_and_reply: null, risk_detection: null, funnel_nodes: null });
          setAnalysisResult(null);
          setIsAnalysisPolling(false);
        }
      })
      .finally(() => {
        if (!cancelled) {
          setIsSessionLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [activeSessionId]);

  useEffect(() => {
    const anyRunning = (Object.values(moduleResults) as (AnalysisResultData | null)[]).some((r) => r?.analysis_status === 'running');
    const shouldPoll = Boolean(activeSessionId) && !isRunningAnalysis && anyRunning;

    if (!shouldPoll || !activeSessionId) {
      setIsAnalysisPolling(false);
      return undefined;
    }

    setIsAnalysisPolling(true);
    const sessionId = activeSessionId;
    let inFlight = false;

    const intervalId = window.setInterval(async () => {
      if (inFlight) {
        return;
      }

      inFlight = true;
      try {
        const updatedResults = await loadLatestAnalysis(sessionId);
        if (activeSessionIdRef.current !== sessionId) {
          return;
        }

        const stillRunning = (Object.values(updatedResults) as (AnalysisResultData | null)[]).some((r) => r?.analysis_status === 'running');
        if (!stillRunning) {
          setIsAnalysisPolling(false);
          window.clearInterval(intervalId);
          await refreshSidebar(sessionId);
        }
      } catch (error) {
        if (activeSessionIdRef.current === sessionId) {
          setNotice({ type: 'error', text: getErrorMessage(error) });
          setIsAnalysisPolling(false);
          setSessionView((current) => ({ ...current, analysisStatus: 'failed' }));
          window.clearInterval(intervalId);
        }
      } finally {
        inFlight = false;
      }
    }, 2000);

    return () => window.clearInterval(intervalId);
  }, [activeSessionId, JSON.stringify(Object.fromEntries((Object.entries(moduleResults) as [string, AnalysisResultData | null][]).map(([k, v]) => [k, v?.analysis_status]))), isRunningAnalysis]);

  async function refreshSidebar(preferredSessionId?: string | null) {
    setIsSidebarRefreshing(true);
    try {
      const sidebarData = await getSidebar();
      const nextItems = sortSidebarItems(sidebarData.items);
      setSidebarItems(nextItems);
      setActiveSessionId((current) => {
        if (preferredSessionId && nextItems.some((item) => item.item_type === 'session' && item.item_id === preferredSessionId)) {
          return preferredSessionId;
        }
        if (current && nextItems.some((item) => item.item_type === 'session' && item.item_id === current)) {
          return current;
        }
        return sidebarData.active_session_id ?? nextItems.find((item) => item.item_type === 'session')?.item_id ?? null;
      });
    } catch (error) {
      setNotice({ type: 'error', text: getErrorMessage(error) });
    } finally {
      setIsSidebarRefreshing(false);
    }
  }

  async function resolveModulePrompt(moduleKey: AnalysisModuleKey): Promise<PromptVersion> {
    const promptData = await listPromptVersions(TOOL_KEY, MODULE_TASK_MAP[moduleKey], moduleKey);
    const draft = modulePromptDrafts[moduleKey];

    const selectedPromptId =
      draft.selectedPromptVersionId && promptData.items.some((item) => item.prompt_version_id === draft.selectedPromptVersionId)
        ? draft.selectedPromptVersionId
        : promptData.active_prompt_version_id ?? promptData.items[0]?.prompt_version_id ?? '';

    const selectedPrompt = promptData.items.find((item) => item.prompt_version_id === selectedPromptId);
    if (!selectedPrompt) {
      throw new Error(`模块「${getModuleLabel(moduleKey)}」未找到可用 Prompt 版本。`);
    }

    const draftText = draft.currentPromptText || selectedPrompt.content;
    if (draftText !== selectedPrompt.content) {
      throw new Error(`模块「${getModuleLabel(moduleKey)}」存在未保留的 Prompt 草稿，请先点击“保留提示词”。`);
    }

    let workingPrompt = selectedPrompt;
    if (!workingPrompt.is_active) {
      const activated = await activatePromptVersion(workingPrompt.prompt_version_id);
      workingPrompt = activated.item;
    }

    if (moduleKey === selectedModuleKey) {
      setPromptVersions(promptData.items.map((item) => (item.prompt_version_id === workingPrompt.prompt_version_id ? workingPrompt : item)));
      setSelectedPromptVersionId(workingPrompt.prompt_version_id);
      setActivePromptVersionId(workingPrompt.prompt_version_id);
      setCurrentPromptText(workingPrompt.content);
    }

    setModulePromptDrafts((current) => ({
      ...current,
      [moduleKey]: {
        selectedPromptVersionId: workingPrompt.prompt_version_id,
        currentPromptText: workingPrompt.content,
      },
    }));
    return workingPrompt;
  }

  async function ensurePromptReady() {
    return resolveModulePrompt(selectedModuleKey);
  }

  function handleNewChat() {
    openUploadModal(null);
    setNotice({ type: 'success', text: '请先上传聊天记录，系统会自动创建并解析会话。' });
  }

  async function handleNewFolder() {
    setContextMenu(null);
    try {
      await createFolder({ title: '新建文件夹', is_pinned: false });
      await refreshSidebar();
      setNotice({ type: 'success', text: '文件夹已创建。' });
    } catch (error) {
      setNotice({ type: 'error', text: getErrorMessage(error) });
    }
  }

  async function handleMoveSessionToFolder(sessionId: string, folderId: string) {
    try {
      await updateSession(sessionId, { folder_id: folderId });
      setExpandedFolderIds((prev) => new Set([...prev, folderId]));
      await refreshSidebar(activeSessionId);
      setNotice({ type: 'success', text: '会话已归档到文件夹。' });
    } catch (error) {
      setNotice({ type: 'error', text: getErrorMessage(error) });
    }
  }

  function handleRenameStart(item: SidebarItem) {
    setEditingItemId(item.item_id);
    setEditingTitle(item.title);
    setContextMenu(null);
  }

  async function handleRenameSave(item: SidebarItem) {
    const nextTitle = editingTitle.trim() || item.title;
    setEditingItemId(null);
    if (nextTitle === item.title) {
      return;
    }

    try {
      if (item.item_type === 'folder') {
        await updateFolder(item.item_id, { title: nextTitle });
      } else {
        await updateSession(item.item_id, { title: nextTitle });
      }
      await refreshSidebar();
      setNotice({ type: 'success', text: '名称已更新。' });
    } catch (error) {
      setNotice({ type: 'error', text: getErrorMessage(error) });
    }
  }

  async function handlePinToggle(item: SidebarItem) {
    setContextMenu(null);
    try {
      if (item.item_type === 'folder') {
        await updateFolder(item.item_id, { is_pinned: !item.is_pinned });
      } else {
        await updateSession(item.item_id, { is_pinned: !item.is_pinned });
      }
      await refreshSidebar();
    } catch (error) {
      setNotice({ type: 'error', text: getErrorMessage(error) });
    }
  }

  async function handleDeleteItem(item: SidebarItem) {
    setContextMenu(null);
    const relatedSessionIds = sidebarItems
      .filter((sidebarItem) => sidebarItem.item_type === 'session' && sidebarItem.folder_id === item.item_id)
      .map((sidebarItem) => sidebarItem.item_id);
    const deletingActiveSession =
      activeSessionId === item.item_id || (item.item_type === 'folder' && relatedSessionIds.includes(activeSessionId || ''));

    const confirmed = window.confirm(
      item.item_type === 'folder'
        ? `确认删除文件夹「${item.title}」吗？${item.session_count ? ` 其下 ${item.session_count} 个会话和分析结果也会一并删除。` : ''}`
        : `确认删除会话「${item.title}」吗？删除后无法恢复。`,
    );

    if (!confirmed) {
      return;
    }

    try {
      if (item.item_type === 'folder') {
        await deleteFolder(item.item_id);
      } else {
        await deleteSession(item.item_id);
      }

      if (deletingActiveSession) {
        activeSessionIdRef.current = null;
        setActiveSessionId(null);
        setSessionView(EMPTY_SESSION_STATE);
        setAnalysisResult(null);
      }

      await refreshSidebar();
      setNotice({
        type: 'success',
        text: item.item_type === 'folder' ? '文件夹已删除。' : '会话已删除。',
      });
    } catch (error) {
      setNotice({ type: 'error', text: getErrorMessage(error) });
    }
  }

  function toggleFolderExpand(folderId: string) {
    setExpandedFolderIds((prev) => {
      const next = new Set(prev);
      if (next.has(folderId)) {
        next.delete(folderId);
      } else {
        next.add(folderId);
      }
      return next;
    });
  }

  function getRootUploadReplaceSessionId(): string | null {
    if (!activeSessionId) {
      return null;
    }

    const activeItem = sidebarItems.find(
      (item) => item.item_type === 'session' && item.item_id === activeSessionId,
    );
    if (!activeItem || activeItem.folder_id || activeItem.title.trim() !== '新对话') {
      return null;
    }

    const isEmptyDraft = sessionView.messages.length === 0 && sessionView.parseStatus === 'pending';
    return isEmptyDraft ? activeItem.item_id : null;
  }

  function closeUploadModal() {
    setIsUploadModalOpen(false);
    setSelectedUploadFolderId(null);
    setUploadReplaceSessionId(null);
  }

  function openUploadModal(folderId: string | null) {
    if (folderId === null) {
      setUploadReplaceSessionId(getRootUploadReplaceSessionId());
    } else {
      setUploadReplaceSessionId(null);
    }
    setSelectedUploadFolderId(folderId);
    setIsUploadModalOpen(true);
    setContextMenu(null);
  }

  async function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    const replacingSessionId = uploadReplaceSessionId;
    setIsUploading(true);
    try {
      const promptVersionId = selectedPromptVersionId || activePromptVersionId;
      const uploadResult = selectedUploadFolderId
        ? await uploadChatRecord(selectedUploadFolderId, file, {
          autoAnalyze: false,
          modelKey: selectedModelKey,
          promptVersionId: promptVersionId || undefined,
        })
        : await importTextSession({
          raw_text: await readFileAsText(file),
          title: stripFileExtension(file.name),
          source_type: 'upload_file',
          auto_analyze: false,
          model_key: selectedModelKey,
          prompt_version_id: promptVersionId || undefined,
        });

      let replaceDeletionFailed = false;
      if (replacingSessionId && replacingSessionId !== uploadResult.session.item_id) {
        try {
          await deleteSession(replacingSessionId);
          setSidebarItems((current) => current.filter((item) => item.item_id !== replacingSessionId));
        } catch {
          replaceDeletionFailed = true;
        }
      }

      upsertSidebarItem(uploadResult.session);
      activeSessionIdRef.current = uploadResult.session.item_id;
      setActiveSessionId(uploadResult.session.item_id);
      setSessionView({
        title: uploadResult.session.title,
        parseStatus: uploadResult.parse_status,
        analysisStatus: 'pending',
        messages: [],
      });
      setAnalysisResult(null);
      closeUploadModal();
      await refreshSidebar(uploadResult.session.item_id);
      await loadSessionMessages(uploadResult.session.item_id, false);
      setNotice({
        type: 'success',
        text: replaceDeletionFailed
          ? `已导入 ${uploadResult.message_count} 条消息，正在触发分析。旧空白会话删除失败，可手动删除。`
          : `已导入 ${uploadResult.message_count} 条消息，正在触发分析。`,
      });
      void runAnalysis('upload_auto', { targetSessionId: uploadResult.session.item_id });
    } catch (error) {
      setNotice({ type: 'error', text: getErrorMessage(error) });
    } finally {
      setIsUploading(false);
      setUploadReplaceSessionId(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  }

  async function handleSavePrompt() {
    const selectedPrompt = promptVersions.find((item) => item.prompt_version_id === selectedPromptVersionId);
    if (!selectedPrompt) {
      setNotice({ type: 'error', text: '当前 Prompt 版本不存在。' });
      return;
    }
    if (currentPromptText === selectedPrompt.content) {
      setNotice({ type: 'success', text: 'Prompt 内容没有变化。' });
      return;
    }

    setIsSavingPrompt(true);
    try {
      const response = await createPromptVersion({
        tool_key: selectedPrompt.tool_key,
        task_key: selectedPrompt.task_key,
        version_label: generateNextVersionLabel(promptVersions),
        version_note: `基于 ${selectedPrompt.version_label} 保留`,
        content: currentPromptText,
        based_on_prompt_version_id: selectedPrompt.prompt_version_id,
        is_active: false,
      });
      setPromptVersions((current) => [response.item, ...current]);
      setSelectedPromptVersionId(response.item.prompt_version_id);
      setCurrentPromptText(response.item.content);
      setModulePromptDrafts((current) => ({
        ...current,
        [selectedModuleKey]: {
          selectedPromptVersionId: response.item.prompt_version_id,
          currentPromptText: response.item.content,
        },
      }));
      setNotice({ type: 'success', text: `已保留提示词版本 ${response.item.version_label}。` });
    } catch (error) {
      setNotice({ type: 'error', text: getErrorMessage(error) });
    } finally {
      setIsSavingPrompt(false);
    }
  }

  async function runAnalysis(
    triggerSource: TriggerSource,
    options?: {
      targetSessionId?: string;
      moduleKeys?: AnalysisModuleKey[];
      silent?: boolean;
      manageRunningState?: boolean;
    },
  ): Promise<boolean> {
    const sessionId = options?.targetSessionId ?? activeSessionId;
    const modulesToRun = options?.moduleKeys ?? [...enabledModules];
    const silent = options?.silent ?? false;
    const manageRunningState = options?.manageRunningState ?? true;

    if (!sessionId) {
      if (!silent) setNotice({ type: 'error', text: '请先选择一个会话。' });
      return false;
    }
    if (!modulesToRun.length) {
      if (!silent) setNotice({ type: 'error', text: '请至少选择一个分析模块。' });
      return false;
    }

    const canUseCurrentMessages = sessionId === activeSessionIdRef.current && sessionView.messages.length > 0;
    if (!canUseCurrentMessages) {
      const messagesData = await loadSessionMessages(sessionId, false);
      if (!messagesData.messages.length) {
        if (!silent) setNotice({ type: 'error', text: '当前会话没有消息，无法执行分析。' });
        return false;
      }
    } else if (!sessionView.messages.length) {
      if (!silent) setNotice({ type: 'error', text: '当前会话没有消息，无法执行分析。' });
      return false;
    }

    if (manageRunningState) setIsRunningAnalysis(true);
    if (activeSessionIdRef.current === sessionId) {
      setSessionView((current) => ({ ...current, analysisStatus: 'running' }));
      setIsAnalysisPolling(true);
    }

    try {
      const allResults = await Promise.allSettled(
        modulesToRun.map(async (moduleKey) => {
          const modelKey = moduleModelKeys[moduleKey] || selectedModelKey;
          if (!modelKey) throw new Error(`模块「${getModuleLabel(moduleKey)}」没有可用模型配置。`);
          const readyPrompt = await resolveModulePrompt(moduleKey);
          const result = await analyzeSession(sessionId, {
            model_key: modelKey,
            prompt_version_id: readyPrompt.prompt_version_id,
            trigger_source: triggerSource,
            module_key: moduleKey,
          });
          return { moduleKey, result };
        }),
      );

      if (activeSessionIdRef.current === sessionId) {
        setModuleResults((current) => {
          const updated = { ...current };
          for (const outcome of allResults) {
            if (outcome.status === 'fulfilled') {
              updated[outcome.value.moduleKey] = outcome.value.result;
            }
          }
          return updated;
        });
        const activeTabOutcome = allResults.find(
          (r) => r.status === 'fulfilled' && r.value.moduleKey === activeResultTab,
        ) as { status: 'fulfilled'; value: { moduleKey: AnalysisModuleKey; result: AnalysisResultData } } | undefined;
        if (activeTabOutcome) {
          setAnalysisResult(activeTabOutcome.value.result);
        }
        const anyRunning = allResults.some(
          (r) => r.status === 'fulfilled' && r.value.result.analysis_status === 'running',
        );
        const anySucceeded = allResults.some((r) => r.status === 'fulfilled');
        setSessionView((current) => ({
          ...current,
          analysisStatus: anyRunning ? 'running' : anySucceeded ? 'succeeded' : 'failed',
        }));
        if (!anyRunning) setIsAnalysisPolling(false);
      }

      await refreshSidebar(sessionId);

      const anySucceeded = allResults.some((r) => r.status === 'fulfilled');
      if (!silent) {
        const anyRunning = allResults.some(
          (r) => r.status === 'fulfilled' && r.value.result.analysis_status === 'running',
        );
        if (anySucceeded) {
          setNotice({
            type: 'success',
            text: anyRunning ? '分析已启动，结果会自动刷新。' : '已完成所有模块分析。',
          });
        } else {
          const firstRejected = allResults.find((r): r is PromiseRejectedResult => r.status === 'rejected');
          setNotice({ type: 'error', text: getErrorMessage(firstRejected?.reason) });
        }
      }
      return anySucceeded;
    } catch (error) {
      if (activeSessionIdRef.current === sessionId) {
        setIsAnalysisPolling(false);
        setSessionView((current) => ({ ...current, analysisStatus: 'failed' }));
      }
      if (!silent) setNotice({ type: 'error', text: getErrorMessage(error) });
      return false;
    } finally {
      if (manageRunningState) setIsRunningAnalysis(false);
    }
  }

  async function handleRunAllModules() {
    await runAnalysis('manual_rerun');
  }

  async function handleApplyAndRerun() {
    if (!activeSessionId) {
      setIsSavingPrompt(true);
      try {
        await ensurePromptReady();
        setIsConfigModalOpen(false);
        setNotice({ type: 'success', text: '配置已应用，当前没有可重跑分析的会话。' });
      } catch (error) {
        setNotice({ type: 'error', text: getErrorMessage(error) });
      } finally {
        setIsSavingPrompt(false);
      }
      return;
    }

    const succeeded = await runAnalysis('prompt_change', { moduleKeys: [selectedModuleKey] });
    if (succeeded) {
      setIsConfigModalOpen(false);
    }
  }

  async function handleCopyReply(content: string) {
    try {
      await navigator.clipboard.writeText(content);
      setNotice({ type: 'success', text: '推荐话术已复制到剪贴板。' });
    } catch {
      setNotice({ type: 'error', text: '复制失败，请检查浏览器剪贴板权限。' });
    }
  }

  const selectedPrompt = promptVersions.find((item) => item.prompt_version_id === selectedPromptVersionId) ?? null;
  const selectedUploadFolder = sidebarItems.find(
    (item) => item.item_type === 'folder' && item.item_id === selectedUploadFolderId,
  );
  const isBusy = isRunningAnalysis || isSavingPrompt || isUploading;
  const currentAnalysisStatus: AnalysisStatus = isRunningAnalysis || isAnalysisPolling || sessionView.analysisStatus === 'running'
    ? 'running'
    : (Object.values(moduleResults) as (AnalysisResultData | null)[]).some((r) => r?.analysis_status === 'succeeded')
      ? 'succeeded'
      : (Object.values(moduleResults) as (AnalysisResultData | null)[]).some((r) => r?.analysis_status === 'failed')
        ? 'failed'
        : sessionView.analysisStatus;

  return (
    <div className="h-screen bg-surface text-on-surface font-body flex flex-col overflow-hidden selection:bg-primary/20">
      <header className="shrink-0 h-16 flex justify-between items-center px-6 md:px-12 bg-surface-container-low border-b border-outline-variant/10 z-50">
        <div className="flex items-center gap-8">
          <span className="text-xl font-black text-primary tracking-tighter cursor-pointer" onClick={() => navigate('/')}>
            Peak Langma 教育 AI 实验室
          </span>
          <nav className="hidden md:flex gap-8 items-center">
            <span className="text-primary border-b-2 border-primary pb-1 font-headline font-bold text-lg cursor-pointer">数据看板</span>
            <button
              onClick={() => setIsConfigModalOpen(true)}
              className="px-4 py-1.5 border border-outline-variant/50 rounded-lg text-sm font-bold text-on-surface hover:bg-surface-container transition-colors flex items-center gap-2 ml-4"
            >
              <Settings size={16} />
              模型、提示词配置
            </button>
          </nav>
        </div>
      </header>

      {notice && (
        <div
          className={`shrink-0 px-6 md:px-12 py-3 text-sm font-medium ${notice.type === 'error' ? 'bg-[#ffdad6] text-[#93000a]' : 'bg-[#d9f8d6] text-[#164b1d]'
            }`}
        >
          {notice.text}
        </div>
      )}

      <main className="flex-1 flex overflow-hidden relative">
        <aside
          className="w-72 bg-surface-container-low flex flex-col border-r border-outline-variant/10 shrink-0 z-20 relative"
          onContextMenu={(event) => {
            event.preventDefault();
            setContextMenu({ x: event.clientX, y: event.clientY, type: 'empty' });
          }}
        >
          <div className="p-6 pb-0 shrink-0">
            <div className="mb-6">
              <h2 className="font-headline font-bold text-primary">教育工作台</h2>
              <p className="text-[10px] text-outline uppercase tracking-widest mt-1">真实接口联调模式</p>
            </div>

            <div className="grid gap-3">
              <button
                onClick={handleNewFolder}
                className="w-full py-3 px-4 bg-primary text-on-primary rounded-xl flex items-center justify-center gap-2 hover:opacity-90 transition-all active:scale-95"
              >
                <FolderPlus size={16} />
                <span className="text-sm font-bold">新建文件夹</span>
              </button>
              <button
                onClick={handleNewChat}
                className="w-full py-3 px-4 bg-surface-container text-on-surface rounded-xl flex items-center justify-center gap-2 hover:bg-surface-container-high transition-all active:scale-95"
              >
                <Plus size={16} />
                <span className="text-sm font-bold">新建对话</span>
              </button>
            </div>
          </div>

          <nav className="flex-1 overflow-y-auto custom-scrollbar px-3 py-4 space-y-1">
            {isInitialLoading ? (
              <div className="flex items-center gap-2 rounded-xl bg-surface-container px-4 py-3 text-sm font-medium text-outline">
                <LoaderCircle size={16} className="animate-spin" />
                正在加载侧栏数据
              </div>
            ) : (() => {
              const folders = sortSidebarItems(sidebarItems.filter((item) => item.item_type === 'folder'));
              const rootSessions = sortSidebarItems(
                sidebarItems.filter((item) => item.item_type === 'session' && !item.folder_id),
              );
              const sessionsByFolder = new Map<string, SidebarItem[]>();
              for (const item of sidebarItems) {
                if (item.item_type === 'session' && item.folder_id) {
                  const list = sessionsByFolder.get(item.folder_id) ?? [];
                  list.push(item);
                  sessionsByFolder.set(item.folder_id, list);
                }
              }
              for (const [folderId, sessions] of sessionsByFolder) {
                sessionsByFolder.set(folderId, sortSidebarItems(sessions));
              }

              const isEmpty = !folders.length && !rootSessions.length;

              function renderSessionRow(item: SidebarItem, indented = false) {
                const isActive = activeSessionId === item.item_id;
                const isDragging = draggingSessionId === item.item_id;
                return (
                  <div
                    key={item.item_id}
                    draggable
                    onDragStart={(event) => {
                      event.dataTransfer.effectAllowed = 'move';
                      event.dataTransfer.setData('text/plain', item.item_id);
                      setDraggingSessionId(item.item_id);
                    }}
                    onDragEnd={() => {
                      setDraggingSessionId(null);
                      setDragOverFolderId(null);
                    }}
                    onClick={() => setActiveSessionId(item.item_id)}
                    onContextMenu={(event) => {
                      event.preventDefault();
                      event.stopPropagation();
                      setContextMenu({ x: event.clientX, y: event.clientY, type: 'item', item });
                    }}
                    className={`${isActive
                      ? 'bg-surface-container-lowest text-primary shadow-sm'
                      : 'text-on-secondary-container hover:bg-surface-container'
                      } rounded-xl font-bold p-3 flex items-center gap-2 cursor-pointer transition-colors ${indented ? 'ml-5' : ''} ${isDragging ? 'opacity-40' : ''}`}
                  >
                    <History size={16} className="shrink-0 opacity-70" />
                    {editingItemId === item.item_id ? (
                      <input
                        autoFocus
                        value={editingTitle}
                        onChange={(event) => setEditingTitle(event.target.value)}
                        onBlur={() => handleRenameSave(item)}
                        onKeyDown={(event) => event.key === 'Enter' && handleRenameSave(item)}
                        className="flex-1 bg-surface border border-primary rounded px-2 py-1 text-sm text-on-surface outline-none"
                        onClick={(event) => event.stopPropagation()}
                      />
                    ) : (
                      <div className="flex-1 min-w-0">
                        <p className="truncate text-sm">{item.title}</p>
                        <p className="mt-0.5 text-[10px] font-medium text-outline">
                          {item.latest_activity_at
                            ? new Date(item.latest_activity_at).toLocaleString('zh-CN', {
                              month: '2-digit',
                              day: '2-digit',
                              hour: '2-digit',
                              minute: '2-digit',
                            })
                            : '等待导入聊天记录'}
                        </p>
                      </div>
                    )}
                    {item.is_pinned && <Pin size={12} className="shrink-0 text-primary" />}
                  </div>
                );
              }

              if (isEmpty) {
                return (
                  <div className="rounded-xl bg-surface-container px-4 py-5 text-sm leading-relaxed text-outline">
                    当前还没有文件夹或会话。先导入一份聊天记录，再触发真实分析。
                  </div>
                );
              }

              return (
                <>
                  {folders.map((folder) => {
                    const isExpanded = expandedFolderIds.has(folder.item_id);
                    const childSessions = sessionsByFolder.get(folder.item_id) ?? [];
                    return (
                      <div key={folder.item_id}>
                        <div
                          onClick={() => toggleFolderExpand(folder.item_id)}
                          onContextMenu={(event) => {
                            event.preventDefault();
                            event.stopPropagation();
                            setContextMenu({ x: event.clientX, y: event.clientY, type: 'item', item: folder });
                          }}
                          onDragOver={(event) => {
                            if (!draggingSessionId) return;
                            event.preventDefault();
                            event.dataTransfer.dropEffect = 'move';
                            setDragOverFolderId(folder.item_id);
                          }}
                          onDragLeave={(event) => {
                            if (!(event.currentTarget as HTMLElement).contains(event.relatedTarget as Node)) {
                              setDragOverFolderId(null);
                            }
                          }}
                          onDrop={(event) => {
                            event.preventDefault();
                            const sessionId = event.dataTransfer.getData('text/plain');
                            setDraggingSessionId(null);
                            setDragOverFolderId(null);
                            if (sessionId && sessionId !== folder.item_id) {
                              void handleMoveSessionToFolder(sessionId, folder.item_id);
                            }
                          }}
                          className={`text-on-secondary-container rounded-xl font-bold p-3 flex items-center gap-2 cursor-pointer transition-colors ${dragOverFolderId === folder.item_id ? 'bg-primary/10 ring-1 ring-primary/30' : 'hover:bg-surface-container'}`}
                        >
                          <span className="shrink-0 text-outline">
                            {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                          </span>
                          {isExpanded ? (
                            <FolderOpen size={16} className="shrink-0 text-primary" />
                          ) : (
                            <Folder size={16} className="shrink-0 text-outline" />
                          )}
                          {editingItemId === folder.item_id ? (
                            <input
                              autoFocus
                              value={editingTitle}
                              onChange={(event) => setEditingTitle(event.target.value)}
                              onBlur={() => handleRenameSave(folder)}
                              onKeyDown={(event) => event.key === 'Enter' && handleRenameSave(folder)}
                              className="flex-1 bg-surface border border-primary rounded px-2 py-1 text-sm text-on-surface outline-none"
                              onClick={(event) => event.stopPropagation()}
                            />
                          ) : (
                            <div className="flex-1 min-w-0">
                              <p className="truncate text-sm">{folder.title}</p>
                              <p className="mt-0.5 text-[10px] font-medium text-outline">
                                {childSessions.length} 个会话
                              </p>
                            </div>
                          )}
                          {folder.is_pinned && <Pin size={12} className="shrink-0 text-primary" />}
                        </div>

                        {isExpanded && (
                          <div className="mt-1 mb-1 space-y-1">
                            {childSessions.length ? (
                              childSessions.map((session) => renderSessionRow(session, true))
                            ) : (
                              <div
                                onClick={() => openUploadModal(folder.item_id)}
                                className="ml-5 rounded-xl border border-dashed border-outline-variant/30 px-3 py-2.5 text-xs text-outline cursor-pointer hover:bg-surface-container hover:text-on-surface transition-colors flex items-center gap-2"
                              >
                                <Upload size={12} />
                                暂无会话，点击导入记录
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}

                  {rootSessions.length > 0 && (
                    <>
                      {folders.length > 0 && (
                        <div className="px-3 pt-3 pb-1">
                          <p className="text-[10px] font-bold text-outline uppercase tracking-widest">未归档会话</p>
                        </div>
                      )}
                      {rootSessions.map((session) => renderSessionRow(session, false))}
                    </>
                  )}
                </>
              );
            })()}
          </nav>

          {contextMenu && (
            <div
              className="fixed bg-surface-container-lowest border border-outline-variant/20 shadow-lg rounded-xl py-2 w-48 z-[100]"
              style={{ top: contextMenu.y, left: contextMenu.x }}
            >
              {contextMenu.type === 'empty' ? (
                <button
                  onClick={handleNewFolder}
                  className="w-full text-left px-4 py-2 text-sm text-on-surface hover:bg-surface-container flex items-center gap-2"
                >
                  <FolderPlus size={16} />
                  新建文件夹
                </button>
              ) : (
                <>
                  {contextMenu.item.item_type === 'folder' && (
                    <button
                      onClick={() => openUploadModal(contextMenu.item.item_id)}
                      className="w-full text-left px-4 py-2 text-sm text-on-surface hover:bg-surface-container flex items-center gap-2"
                    >
                      <Upload size={16} />
                      上传对话记录
                    </button>
                  )}
                  <button
                    onClick={() => handleRenameStart(contextMenu.item)}
                    className="w-full text-left px-4 py-2 text-sm text-on-surface hover:bg-surface-container flex items-center gap-2"
                  >
                    <Save size={16} />
                    重命名
                  </button>
                  <button
                    onClick={() => handlePinToggle(contextMenu.item)}
                    className="w-full text-left px-4 py-2 text-sm text-on-surface hover:bg-surface-container flex items-center gap-2"
                  >
                    <Pin size={16} />
                    {contextMenu.item.is_pinned ? '取消置顶' : '置顶'}
                  </button>
                  <button
                    onClick={() => handleDeleteItem(contextMenu.item)}
                    className="w-full text-left px-4 py-2 text-sm text-[#ba1a1a] hover:bg-[#ffdad6]/60 flex items-center gap-2"
                  >
                    <Trash2 size={16} />
                    {contextMenu.item.item_type === 'folder' ? '删除文件夹' : '删除会话'}
                  </button>
                </>
              )}
            </div>
          )}

          <div className="p-6 pt-4 border-t border-outline-variant/10 shrink-0">
            <button
              onClick={() => navigate(-1)}
              className="w-full py-3 px-4 bg-surface-container hover:bg-surface-container-high text-on-surface rounded-xl flex items-center justify-center gap-2 transition-all active:scale-95 font-bold text-sm shadow-sm"
            >
              <ArrowLeft size={16} />
              返回上一页
            </button>
          </div>
        </aside>

        <section className="flex-1 flex flex-col bg-surface relative z-10 overflow-hidden">
          <div className="absolute inset-0 grid-bg pointer-events-none opacity-10"></div>
          <div className="absolute inset-0 grain-overlay pointer-events-none opacity-[0.02]"></div>

          <div className="p-6 md:p-8 border-b border-outline-variant/10 flex justify-between items-center bg-surface/80 backdrop-blur-md z-20 shrink-0 gap-4">
            <div>
              <h1 className="font-headline text-2xl font-bold text-on-surface">对话预览</h1>
              <p className="text-sm text-outline mt-1">
                {activeSessionId
                  ? `${sessionView.title || '当前会话'} · 共 ${sessionView.messages.length} 条消息`
                  : '请选择会话，或先导入一份聊天记录'}
              </p>
            </div>
            <div className="flex flex-wrap justify-end gap-2">
              <span className="px-3 py-1 bg-secondary-container text-on-secondary-container text-[10px] font-bold rounded-full">
                {getParseStatusLabel(sessionView.parseStatus)}
              </span>
              <span className="px-3 py-1 bg-[#acf4a4] text-[#002203] text-[10px] font-bold rounded-full">
                {getAnalysisStatusLabel(currentAnalysisStatus)}
              </span>
              <button
                onClick={() => openUploadModal(null)}
                className="px-3 py-1 border border-outline-variant/30 text-on-surface text-[10px] font-bold rounded-full hover:bg-surface-container transition-colors"
              >
                导入记录
              </button>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto custom-scrollbar p-6 md:p-8 space-y-8 relative z-10">
            {isSessionLoading ? (
              <div className="flex items-center justify-center h-full text-outline text-sm font-bold gap-2">
                <LoaderCircle size={18} className="animate-spin" />
                正在加载会话消息
              </div>
            ) : sessionView.messages.length ? (
              sessionView.messages.map((message) => {
                const appearance = getSpeakerAppearance(message.speaker_role);
                return (
                  <div key={message.message_id} className={`flex flex-col ${appearance.align} max-w-[85%]`}>
                    <div className={`flex items-center gap-2 mb-2 ${appearance.reverse}`}>
                      <span className={`w-6 h-6 rounded flex items-center justify-center text-[10px] font-bold ${appearance.badge}`}>
                        {appearance.label}
                      </span>
                      <span className={`text-xs font-bold ${appearance.name}`}>{message.speaker_name || '未识别角色'}</span>
                      <span className="text-[10px] text-outline">{formatMessageTime(message)}</span>
                    </div>
                    <div className={`${appearance.bubble} p-4 rounded-2xl text-sm leading-relaxed shadow-sm`}>
                      {message.content}
                    </div>
                    {message.parse_note && <p className="mt-2 text-[10px] font-medium text-outline">解析备注：{message.parse_note}</p>}
                  </div>
                );
              })
            ) : (
              <div className="flex flex-col items-center justify-center h-full gap-4 text-center">
                <div className="w-16 h-16 bg-surface-container rounded-full flex items-center justify-center text-primary">
                  <FileText size={28} />
                </div>
                <div>
                  <p className="text-on-surface font-bold">当前没有可展示的对话记录</p>
                  <p className="mt-2 text-sm leading-relaxed text-outline">导入聊天文本后，这里会展示后端解析后的真实消息列表。</p>
                </div>
                <button
                  onClick={() => openUploadModal(null)}
                  className="px-5 py-2.5 bg-primary text-on-primary rounded-xl text-sm font-bold hover:opacity-90 transition-opacity"
                >
                  导入聊天记录
                </button>
              </div>
            )}
          </div>
        </section>

        <aside className="w-[420px] bg-surface-container-low border-l border-outline-variant/10 shrink-0 z-20 flex flex-col">
          <div className="p-6 md:p-8 pb-4 shrink-0 border-b border-outline-variant/10 bg-surface-container-low z-10">
            <div className="flex items-center justify-between gap-4">
              <div>
                <h3 className="font-headline font-bold text-lg text-primary flex items-center gap-2">
                  <BarChart2 size={20} />
                  智能画像分析
                </h3>
                <p className="mt-2 text-xs text-outline">
                  {moduleResults[activeResultTab]
                    ? `${moduleResults[activeResultTab]!.model.model_label} · ${moduleResults[activeResultTab]!.prompt_version.version_label}`
                    : '尚未读取到分析结果'}
                </p>
              </div>
              <button
                onClick={handleRunAllModules}
                disabled={!activeSessionId || !sessionView.messages.length || isBusy}
                className="px-4 py-2.5 bg-primary text-on-primary rounded-xl text-sm font-bold hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {isRunningAnalysis ? <LoaderCircle size={16} className="animate-spin" /> : <Zap size={16} fill="currentColor" />}
                运行已选模块
              </button>
            </div>
          </div>

          {/* Result module tabs */}
          <div className="shrink-0 flex border-b border-outline-variant/10 bg-surface-container-low px-2">
            {MODULE_OPTIONS.map((module) => {
              const tabResult = moduleResults[module.key];
              const tabStatus = tabResult?.analysis_status ?? 'pending';
              const isEnabled = enabledModules.has(module.key);
              const isActive = activeResultTab === module.key;
              return (
                <button
                  key={module.key}
                  onClick={() => setActiveResultTab(module.key)}
                  className={`py-3 px-3 text-[11px] font-bold border-b-2 transition-colors flex items-center gap-1.5 whitespace-nowrap ${isActive
                    ? 'border-primary text-primary'
                    : 'border-transparent text-outline hover:text-on-surface'
                    } ${!isEnabled ? 'opacity-40' : ''}`}
                >
                  {module.label}
                  {tabStatus === 'running' && <LoaderCircle size={10} className="animate-spin text-primary shrink-0" />}
                  {tabStatus === 'succeeded' && <span className="w-1.5 h-1.5 rounded-full bg-[#0c5216] shrink-0" />}
                  {tabStatus === 'failed' && <span className="w-1.5 h-1.5 rounded-full bg-[#ba1a1a] shrink-0" />}
                </button>
              );
            })}
          </div>

          <div className="flex-1 overflow-y-auto custom-scrollbar p-6 md:p-8 flex flex-col gap-6">
            {!activeSessionId ? (
              <div className="rounded-xl bg-surface-container-lowest p-6 text-sm leading-relaxed text-outline">
                先选择一个会话，或者导入聊天记录，右侧就会加载数据库中的 真实分析结果。
              </div>
            ) : isSessionLoading && !moduleResults[activeResultTab] ? (
              <div className="rounded-xl bg-surface-container-lowest p-6 text-sm font-medium text-outline flex items-center gap-2">
                <LoaderCircle size={16} className="animate-spin" />
                正在拉取分析结果
              </div>
            ) : (() => {
              const tabResult = moduleResults[activeResultTab];
              const tabRisk = getRiskPresentation(tabResult?.risk_assessment.level ?? 'unknown');
              const isTabPending = isRunningAnalysis || (isAnalysisPolling && tabResult?.analysis_status === 'running');

              if (!tabResult) {
                return (
                  <div className="rounded-xl bg-surface-container-lowest p-6 text-sm leading-relaxed text-outline">
                    当前没有分析结果。你可以在上传时自动分析，或点击右上角"运行已选模块"。
                  </div>
                );
              }

              const summaryBlock = (
                <div className="bg-surface-container-lowest p-5 rounded-xl shadow-sm">
                  <div className="mb-3 flex items-center justify-between gap-3">
                    <p className="text-[10px] font-bold text-outline uppercase tracking-tighter">会话摘要</p>
                    {isTabPending && (
                      <span className="inline-flex items-center gap-2 rounded-full bg-[#e6f4ec] px-3 py-1 text-[10px] font-bold text-[#0c5216]">
                        <LoaderCircle size={12} className="animate-spin" />
                        分析进行中
                      </span>
                    )}
                  </div>
                  <p className="text-sm leading-relaxed text-on-surface">
                    {isTabPending
                      ? tabResult.summary || '正在执行分析，结果会自动刷新。'
                      : tabResult.summary || '当前暂无摘要。'}
                  </p>
                </div>
              );

              if (activeResultTab === 'user_profile_and_reply') {
                return (
                  <>
                    {summaryBlock}
                    <div className="bg-surface-container-lowest p-5 rounded-xl shadow-sm">
                      <p className="text-[10px] font-bold text-outline mb-3 uppercase tracking-tighter">用户标签</p>
                      {tabResult.persona_tags.length ? (
                        <div className="grid gap-3">
                          {tabResult.persona_tags.map((item) => (
                            <div key={item.finding_id} className="rounded-xl bg-surface px-4 py-4">
                              <div className="flex items-center justify-between gap-3">
                                <span className="rounded-full bg-[#afefdd] px-3 py-1 text-xs font-bold text-[#00201a]">{item.title}</span>
                                <span className="text-[10px] font-bold text-outline">{Math.round(item.confidence * 100)}%</span>
                              </div>
                              <p className="mt-3 text-sm leading-relaxed text-on-surface-variant">{item.summary}</p>
                              <p className="mt-2 text-xs leading-relaxed text-outline">判断理由：{item.reason}</p>
                              <EvidenceList evidences={item.evidences} />
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-sm text-outline">当前分析未提取到用户标签。</p>
                      )}
                    </div>
                    <SmartReplySection replies={tabResult.smart_replies} onCopy={handleCopyReply} />
                  </>
                );
              }

              if (activeResultTab === 'risk_detection') {
                return (
                  <>
                    {summaryBlock}
                    <div className={`${tabRisk.panel} p-5 rounded-xl`}>
                      <div className="flex items-center justify-between mb-3">
                        <p className={`text-[10px] font-bold uppercase tracking-tighter ${tabRisk.text}`}>流失风险评估</p>
                        <span className={`text-sm font-bold ${tabRisk.text}`}>
                          {tabRisk.label}风险 ({tabResult.risk_assessment.score}%)
                        </span>
                      </div>
                      <div className="w-full bg-surface-container h-1.5 rounded-full mb-4 overflow-hidden">
                        <div
                          className={`${tabRisk.bar} h-full rounded-full`}
                          style={{ width: `${Math.max(0, Math.min(tabResult.risk_assessment.score, 100))}%` }}
                        />
                      </div>
                      <p className={`text-xs leading-relaxed ${tabRisk.softText}`}>{tabResult.risk_assessment.summary}</p>
                      <p className={`mt-3 text-xs leading-relaxed ${tabRisk.softText}`}>判断原因：{tabResult.risk_assessment.reason}</p>
                      <EvidenceList evidences={tabResult.risk_assessment.evidences} />
                    </div>
                  </>
                );
              }

              if (activeResultTab === 'funnel_nodes') {
                return (
                  <>
                    {summaryBlock}
                    <FindingSection
                      title="核心痛点"
                      emptyText="当前分析未识别到明确痛点。"
                      accentClass="border-primary"
                      items={tabResult.pain_points}
                    />
                    <FindingSection
                      title="成交节点"
                      emptyText="当前分析未识别到明确成交节点。"
                      accentClass="border-[#064f13]"
                      items={tabResult.deal_closing_points}
                    />
                    <FindingSection
                      title="流失节点"
                      emptyText="当前分析未识别到明确流失节点。"
                      accentClass="border-[#ba1a1a]"
                      items={tabResult.churn_points}
                    />
                    <FindingSection
                      title="高频关注点"
                      emptyText="当前分析未识别到高频关注点。"
                      accentClass="border-[#004d40]"
                      items={tabResult.high_frequency_points}
                    />
                  </>
                );
              }

              return null;
            })()}
          </div>
        </aside>
      </main>

      {isConfigModalOpen && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[100] flex items-center justify-center p-4">
          <div className="bg-surface w-full max-w-2xl rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
            <div className="p-6 border-b border-outline-variant/10 flex justify-between items-center bg-surface-container-lowest">
              <h2 className="font-headline font-bold text-xl text-on-surface flex items-center gap-2">
                <Settings size={20} className="text-primary" />
                模型与提示词配置
              </h2>
              <button onClick={() => setIsConfigModalOpen(false)} className="p-2 hover:bg-surface-container rounded-full transition-colors">
                <X size={20} className="text-outline" />
              </button>
            </div>

            <div className="p-6 overflow-y-auto custom-scrollbar flex flex-col gap-6">
              {/* Module tabs */}
              <div className="-mx-6 -mt-6 px-6 pt-0 pb-0 border-b border-outline-variant/10">
                <div className="flex gap-0">
                  {MODULE_OPTIONS.map((module) => (
                    <button
                      key={module.key}
                      onClick={() => setSelectedModuleKey(module.key)}
                      className={`py-3 px-4 text-sm font-bold border-b-2 transition-colors whitespace-nowrap ${selectedModuleKey === module.key
                        ? 'border-primary text-primary'
                        : 'border-transparent text-outline hover:text-on-surface'
                        }`}
                    >
                      {module.label}
                    </button>
                  ))}
                </div>
              </div>

              <label className="flex items-center gap-3 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={enabledModules.has(selectedModuleKey)}
                  onChange={(event) => {
                    setEnabledModules((prev) => {
                      const next = new Set(prev);
                      if (event.target.checked) {
                        next.add(selectedModuleKey);
                      } else {
                        next.delete(selectedModuleKey);
                      }
                      return next;
                    });
                  }}
                  className="w-4 h-4 rounded border-outline-variant accent-primary cursor-pointer"
                />
                <span className="text-sm text-on-surface">运行时包含此模块</span>
              </label>

              <div className="flex flex-col gap-2">
                <label className="text-xs font-bold text-outline uppercase tracking-wider">推理模型</label>
                <div className="relative">
                  <select
                    value={selectedModelKey}
                    onChange={(event) => {
                      const nextModelKey = event.target.value;
                      setSelectedModelKey(nextModelKey);
                      setModuleModelKeys((current) => ({
                        ...current,
                        [selectedModuleKey]: nextModelKey,
                      }));
                    }}
                    className="w-full bg-surface-container border border-outline-variant/50 text-sm rounded-xl py-3 pl-4 pr-10 appearance-none focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all text-on-surface"
                  >
                    {modelOptions.map((model) => (
                      <option key={model.model_key} value={model.model_key}>
                        {model.model_label}
                        {model.is_default ? '（默认）' : ''}
                      </option>
                    ))}
                  </select>
                  <ChevronDown className="absolute right-4 top-3.5 text-outline pointer-events-none" size={16} />
                </div>
              </div>

              <div className="flex flex-col gap-2">
                <label className="text-xs font-bold text-outline uppercase tracking-wider">当前分析 Prompt 版本</label>
                <div className="relative">
                  <select
                    value={selectedPromptVersionId}
                    onChange={(event) => {
                      const nextVersionId = event.target.value;
                      const nextContent = promptVersions.find((item) => item.prompt_version_id === nextVersionId)?.content ?? '';
                      setSelectedPromptVersionId(nextVersionId);
                      setCurrentPromptText(nextContent);
                      setModulePromptDrafts((current) => ({
                        ...current,
                        [selectedModuleKey]: {
                          selectedPromptVersionId: nextVersionId,
                          currentPromptText: nextContent,
                        },
                      }));
                    }}
                    className="w-full bg-surface-container border border-outline-variant/50 text-sm rounded-xl py-3 pl-4 pr-10 appearance-none focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all text-on-surface"
                  >
                    {promptVersions.map((promptVersion) => (
                      <option key={promptVersion.prompt_version_id} value={promptVersion.prompt_version_id}>
                        {promptVersion.version_label}
                        {promptVersion.is_active ? '（当前启用）' : ''}
                        {promptVersion.version_note ? ` · ${promptVersion.version_note}` : ''}
                      </option>
                    ))}
                  </select>
                  <ChevronDown className="absolute right-4 top-3.5 text-outline pointer-events-none" size={16} />
                </div>
              </div>

              <div className="rounded-xl bg-surface-container-lowest px-4 py-3 text-xs leading-relaxed text-outline">
                当前启用版本：{activePromptVersionId ? promptVersions.find((item) => item.prompt_version_id === activePromptVersionId)?.version_label ?? '未知' : '未设置'}
                {selectedPrompt?.version_note ? ` · ${selectedPrompt.version_note}` : ''}
              </div>

              <div className="flex flex-col gap-2 flex-1">
                <div className="flex justify-between items-center">
                  <label className="text-xs font-bold text-outline uppercase tracking-wider">当前 Prompt 内容</label>
                  <button
                    onClick={handleSavePrompt}
                    disabled={isSavingPrompt || !selectedPromptVersionId}
                    className="text-xs text-primary font-bold hover:underline flex items-center gap-1 disabled:opacity-50 disabled:no-underline"
                  >
                    {isSavingPrompt ? <LoaderCircle size={12} className="animate-spin" /> : <Save size={12} />}
                    保留提示词
                  </button>
                </div>
                <textarea
                  value={currentPromptText}
                  onChange={(event) => {
                    const nextText = event.target.value;
                    setCurrentPromptText(nextText);
                    setModulePromptDrafts((current) => ({
                      ...current,
                      [selectedModuleKey]: {
                        selectedPromptVersionId: selectedPromptVersionId,
                        currentPromptText: nextText,
                      },
                    }));
                  }}
                  className="w-full h-64 bg-surface-container-lowest border border-outline-variant/50 rounded-xl p-4 text-sm text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all resize-none font-mono leading-relaxed"
                />
              </div>
            </div>

            <div className="p-6 border-t border-outline-variant/10 bg-surface-container-lowest flex justify-end gap-3">
              <button
                onClick={() => setIsConfigModalOpen(false)}
                className="px-6 py-2.5 rounded-xl font-bold text-sm text-on-surface hover:bg-surface-container transition-colors"
              >
                取消
              </button>
              <button
                onClick={handleApplyAndRerun}
                disabled={isBusy || !selectedPromptVersionId || !selectedModelKey}
                className="px-6 py-2.5 bg-primary text-on-primary rounded-xl font-bold text-sm hover:opacity-90 transition-opacity flex items-center gap-2 shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isBusy ? <LoaderCircle size={16} className="animate-spin" /> : <Zap size={16} fill="currentColor" />}
                应用并重新运行
              </button>
            </div>
          </div>
        </div>
      )}

      {isUploadModalOpen && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[100] flex items-center justify-center p-4">
          <div className="bg-surface w-full max-w-md rounded-2xl shadow-2xl overflow-hidden flex flex-col">
            <div className="p-6 border-b border-outline-variant/10 flex justify-between items-center bg-surface-container-lowest">
              <h2 className="font-headline font-bold text-xl text-on-surface flex items-center gap-2">
                <Upload size={20} className="text-primary" />
                上传对话记录
              </h2>
              <button onClick={closeUploadModal} className="p-2 hover:bg-surface-container rounded-full transition-colors">
                <X size={20} className="text-outline" />
              </button>
            </div>

            <div className="p-8 flex flex-col items-center justify-center gap-4">
              <div className="w-16 h-16 bg-primary-container rounded-full flex items-center justify-center text-primary mb-2">
                <FileText size={32} />
              </div>
              <p className="text-center text-on-surface font-bold">拖拽文件到此处，或点击上传</p>
              <p className="text-center text-outline text-sm leading-relaxed">
                支持 .txt、.csv、.json、.md、.log。
                <br />
                {selectedUploadFolder
                  ? `将导入到文件夹「${selectedUploadFolder.title}」并自动触发分析。`
                  : uploadReplaceSessionId
                    ? '上传后会替换当前空白“新对话”，并自动触发分析。'
                    : '未指定文件夹时，将直接创建根级会话并自动触发分析。'}
              </p>
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileChange}
                accept={SUPPORTED_UPLOAD_ACCEPT}
                className="hidden"
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={isUploading}
                className="mt-4 px-6 py-2.5 bg-primary text-on-primary rounded-xl font-bold text-sm hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {isUploading ? <LoaderCircle size={16} className="animate-spin" /> : <Upload size={16} />}
                选择文件
              </button>
            </div>
          </div>
        </div>
      )}

      {(isSidebarRefreshing || isInitialLoading) && (
        <div className="fixed bottom-6 right-6 rounded-full bg-surface-container-lowest border border-outline-variant/20 px-4 py-2 shadow-lg text-xs font-bold text-outline flex items-center gap-2 z-[120]">
          <LoaderCircle size={14} className="animate-spin" />
          正在同步数据
        </div>
      )}
    </div>
  );
}
