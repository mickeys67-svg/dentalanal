import axios from 'axios';
import {
    User,
    KPI,
    DashboardKPI,
    Campaign,
    Connector,
    Client,
    PlatformType,
    KeywordRank,
    SOVAnalysisResult,
    UserCreate,
    CompetitorAnalysisResult,
    PlatformConnection,
    SWOTData,
    StrategyGoal,
    CollaborativeTask,
    ApprovalRequest,
    ReportTemplate,
    FunnelStage,
    CohortRow,
    AttributionData,
    SegmentRow,
    Settlement,
    EfficiencyReview
} from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://BACKEND_URL_NOT_SET';

export const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add a request interceptor to include the auth token
api.interceptors.request.use((config) => {
    // Skip auth header for login and signup endpoints to prevent old tokens from causing issues
    if (config.url?.includes('/auth/login') || (config.url?.includes('/users/') && config.method === 'post')) {
        return config;
    }

    if (typeof window !== 'undefined') {
        const token = localStorage.getItem('token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
    }
    return config;
}, (error) => {
    return Promise.reject(error);
});

// [FIX Issue #1] Response interceptor: auto-refresh tokens on 401
let isRefreshing = false;
let refreshSubscribers: Array<(token: string) => void> = [];

const subscribeTokenRefresh = (cb: (token: string) => void) => {
    refreshSubscribers.push(cb);
};

const onRefreshed = (token: string) => {
    refreshSubscribers.forEach((cb) => cb(token));
    refreshSubscribers = [];
};

api.interceptors.response.use(
    (response) => response,
    async (error) => {
        // 상세한 에러 로깅
        console.error('❌ API Error Response:', {
            status: error.response?.status,
            statusText: error.response?.statusText,
            url: error.config?.url,
            method: error.config?.method,
            dataType: typeof error.response?.data,
            dataLength: error.response?.data?.length || 'N/A',
            contentType: error.response?.headers?.['content-type'],
            firstChars: error.response?.data?.toString?.()?.substring(0, 100)
        });

        // [NEW] Handle 401: Try to refresh token
        if (error.response?.status === 401 && typeof window !== 'undefined') {
            const originalRequest = error.config;

            if (!originalRequest._retry && !originalRequest.url?.includes('/auth/')) {
                originalRequest._retry = true;

                if (!isRefreshing) {
                    isRefreshing = true;

                    try {
                        const refreshToken = localStorage.getItem('refreshToken');

                        if (!refreshToken) {
                            throw new Error('No refresh token available');
                        }

                        // Call refresh endpoint
                        const response = await axios.post(
                            `${API_BASE_URL}/api/v1/auth/refresh`,
                            { refresh_token: refreshToken },
                            { headers: { 'Content-Type': 'application/json' } }
                        );

                        const { access_token, refresh_token } = response.data;

                        // Store new tokens
                        localStorage.setItem('token', access_token);
                        localStorage.setItem('refreshToken', refresh_token);

                        // Update default header
                        api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;

                        isRefreshing = false;
                        onRefreshed(access_token);

                        // Retry original request with new token
                        originalRequest.headers['Authorization'] = `Bearer ${access_token}`;
                        return api(originalRequest);
                    } catch (refreshError) {
                        // Refresh failed - logout user
                        isRefreshing = false;
                        localStorage.removeItem('token');
                        localStorage.removeItem('refreshToken');
                        localStorage.removeItem('user');
                        window.location.href = '/login';
                        return Promise.reject(refreshError);
                    }
                } else {
                    // Another request is already refreshing, wait for it
                    return new Promise((resolve) => {
                        subscribeTokenRefresh((newToken: string) => {
                            originalRequest.headers['Authorization'] = `Bearer ${newToken}`;
                            resolve(api(originalRequest));
                        });
                    });
                }
            } else if (window.location.pathname !== '/login') {
                // Token refresh failed or is auth endpoint
                localStorage.removeItem('token');
                localStorage.removeItem('refreshToken');
                localStorage.removeItem('user');
                window.location.href = '/login';
            }
        }

        return Promise.reject(error);
    }
);

export const scrapePlace = async (keyword: string, clientId?: string): Promise<{ message: string }> => {
    const response = await api.post('/api/v1/scrape/place', { keyword, client_id: clientId });
    return response.data;
};

export const scrapeView = async (keyword: string, clientId?: string): Promise<{ message: string }> => {
    const response = await api.post('/api/v1/scrape/view', { keyword, client_id: clientId });
    return response.data;
};

export const getScrapeResults = async (
    clientId: string,
    keyword: string,
    platform: string = 'NAVER_PLACE'
): Promise<{
    has_data: boolean;
    keyword: string;
    platform: string;
    results: Array<{
        target_id: string;
        target_name: string;
        target_type: string;
        rank: number;
        rank_change: number;
        captured_at: string;
    }>;
    total_count: number;
    message: string;
}> => {
    const response = await api.get('/api/v1/scrape/results', {
        params: {
            client_id: clientId,
            keyword,
            platform
        }
    });
    return response.data;
};

export const analyzeSOV = async (params: { target_hospital: string, keywords: string[], top_n?: number, platform?: string }): Promise<SOVAnalysisResult[]> => {
    const response = await api.post('/api/v1/analyze/sov', params);
    return response.data;
};

export const getRankings = async (keyword: string, platform: string = 'NAVER_PLACE'): Promise<KeywordRank[]> => {
    const response = await api.post('/api/v1/analyze/rankings', {
        keyword,
        platform
    });
    return response.data;
};

export const getCompetitors = async (keyword: string, platform: string = 'NAVER_PLACE', topN: number = 10): Promise<CompetitorAnalysisResult> => {
    const response = await api.post('/api/v1/analyze/competitors', {
        keyword,
        platform,
        top_n: topN
    });
    return response.data;
};

export const getRankingTrend = async (params: { keyword: string, target_hospital: string, platform?: string, days?: number }): Promise<{ date: string, rank: number }[]> => {
    const response = await api.get('/api/v1/analyze/ranking-trend', { params });
    return response.data;
};

export const getAIReport = async (keyword: string, targetHospital: string, platform: string = 'NAVER_PLACE', topN: number = 10): Promise<{ report: string }> => {
    const response = await api.post('/api/v1/analyze/ai-report', {
        keyword,
        target_hospital: targetHospital,
        platform,
        top_n: topN
    });
    return response.data;
};

// --- Dashboard & Management ---

export interface DashboardSummary {
    kpis: DashboardKPI[];
    campaigns: Campaign[];
    sov_data: { name: string; value: number }[];
    is_sample?: boolean;
    last_keyword?: string;
}

export const getDashboardSummary = async (clientId?: string): Promise<DashboardSummary> => {
    const response = await api.get('/api/v1/dashboard/summary', {
        params: { client_id: clientId }
    });
    return response.data;
};

export const getMetricsTrend = async (clientId?: string): Promise<any[]> => {
    const response = await api.get('/api/v1/dashboard/metrics/trend', {
        params: { client_id: clientId }
    });
    return response.data.trend || [];
};

export const getConnectors = async (): Promise<{ connectors: Connector[] }> => {
    const response = await api.get(`/api/v1/connectors/`);
    return response.data;
};

export const getClients = async (): Promise<Client[]> => {
    const response = await api.get('/api/v1/clients/');
    return response.data;
};

export const createClient = async (data: Partial<Client>): Promise<Client> => {
    const response = await api.post('/api/v1/clients/', data);
    return response.data;
};

export const deleteClient = async (clientId: string): Promise<{ status: string }> => {
    const response = await api.delete(`/api/v1/clients/${clientId}`);
    return response.data;
};

export const updateClient = async (
    clientId: string,
    data: { email?: string; name?: string; industry?: string; conversion_value?: number; fee_rate?: number }
): Promise<Client> => {
    const response = await api.patch(`/api/v1/clients/${clientId}`, data);
    return response.data;
};

export interface SendReportEmailPayload {
    report_id: string;
    to_emails: string[];
    subject: string;
    summary: string;
}

export const sendReportEmail = async (
    payload: SendReportEmailPayload
): Promise<{ status: string; message: string }> => {
    const response = await api.post('/api/v1/reports/send-email', payload);
    return response.data;
};

export const updateBulkTargets = async (data: { client_id: string, targets: any[] }): Promise<{ status: string, targets: any[] }> => {
    const response = await api.post('/api/v1/analyze/targets/bulk', data);
    return response.data;
};

export const getActiveConnections = async (clientId: string): Promise<PlatformConnection[]> => {
    const response = await api.get(`/api/v1/connectors/active/${clientId}`);
    return response.data;
};

export const connectPlatform = async (platformId: string, clientId: string, credentials: Record<string, string>): Promise<{ status: string; message: string }> => {
    const response = await api.post(`/api/v1/connectors/connect/${platformId}`, credentials, {
        params: { client_id: clientId }
    });
    return response.data;
};

// --- Strategy APIs ---

export const getSWOT = async (clientId: string): Promise<SWOTData> => {
    const response = await api.get(`/api/v1/strategy/swot/${clientId}`);
    return response.data;
};

export const saveSWOT = async (clientId: string, data: SWOTData): Promise<SWOTData> => {
    const response = await api.post(`/api/v1/strategy/swot/${clientId}`, data);
    return response.data;
};

export const getStrategyGoals = async (clientId: string): Promise<StrategyGoal[]> => {
    const response = await api.get(`/api/v1/strategy/goals/${clientId}`);
    return response.data;
};

export const createStrategyGoal = async (clientId: string, data: Partial<StrategyGoal>): Promise<StrategyGoal> => {
    const response = await api.post(`/api/v1/strategy/goals/${clientId}`, data);
    return response.data;
};

// --- Collaboration APIs ---

export const getCollaborativeTasks = async (clientId: string): Promise<CollaborativeTask[]> => {
    const response = await api.get(`/api/v1/collaboration/tasks/${clientId}`);
    return response.data;
};

export const createCollaborativeTask = async (clientId: string, data: Partial<CollaborativeTask>): Promise<CollaborativeTask> => {
    const response = await api.post(`/api/v1/collaboration/tasks/${clientId}`, data);
    return response.data;
};

export const getTaskComments = async (taskId: string): Promise<any[]> => {
    const response = await api.get(`/api/v1/collaboration/tasks/detail/${taskId}/comments`);
    return response.data;
};

export const createTaskComment = async (taskId: string, content: string): Promise<any> => {
    const response = await api.post(`/api/v1/collaboration/tasks/detail/${taskId}/comments`, { content });
    return response.data;
};

export const getNotifications = async (): Promise<any[]> => {
    const response = await api.get('/api/v1/notifications');
    return response.data;
};

export const markAsRead = async (id: string): Promise<void> => {
    await api.post(`/api/v1/notifications/${id}/read`);
};

export const markAllAsRead = async (): Promise<void> => {
    await api.post('/api/v1/notifications/read-all');
};

export const getNotices = async (): Promise<any[]> => {
    const response = await api.get('/api/v1/collaboration/notices');
    return response.data;
};

export const createNotice = async (data: { title: string, content: string, is_pinned?: boolean }): Promise<any> => {
    const response = await api.post('/api/v1/collaboration/notices', data);
    return response.data;
};

export const getApprovalRequests = async (clientId: string): Promise<ApprovalRequest[]> => {
    const response = await api.get(`/api/v1/collaboration/approvals/${clientId}`);
    return response.data;
};

// Report Templates
export const getReportTemplates = async (): Promise<ReportTemplate[]> => {
    const response = await api.get('/api/v1/reports/templates');
    return response.data;
};

export const createReportTemplate = async (data: Partial<ReportTemplate>): Promise<ReportTemplate> => {
    const response = await api.post('/api/v1/reports/templates', data);
    return response.data;
};

export const updateReportTemplate = async (id: string, data: Partial<ReportTemplate>): Promise<ReportTemplate> => {
    const response = await api.put(`/api/v1/reports/templates/${id}`, data);
    return response.data;
};

export const deleteReportTemplate = async (id: string): Promise<void> => {
    await api.delete(`/api/v1/reports/templates/${id}`);
};

export const takeApprovalAction = async (requestId: string, action: 'APPROVED' | 'REJECTED'): Promise<{ status: string }> => {
    const response = await api.post(`/api/v1/collaboration/approvals/${requestId}/action`, null, {
        params: { action }
    });
    return response.data;
};

// --- Automation & AI ---

export const generateAdCopy = async (data: { swot_data: SWOTData; target_audience: string; key_proposition: string }): Promise<Array<{ content: string }>> => {
    const response = await api.post(`/api/v1/automation/generate-copy`, data);
    return response.data;
};

export const getAIRecommendations = async (campaigns: Campaign[]): Promise<string> => {
    const response = await api.post(`/api/v1/automation/recommendations`, { campaigns });
    return response.data;
};

export const triggerSync = async (): Promise<{ status: string; message: string }> => {
    const response = await api.post(`/api/v1/automation/sync`);
    return response.data;
};

// --- Deep Analysis ---
export const getFunnelData = async (clientId: string): Promise<FunnelStage[]> => {
    const response = await api.get(`/api/v1/analyze/funnel/${clientId}`);
    return response.data;
};

export const getCohortData = async (clientId: string): Promise<CohortRow[]> => {
    const response = await api.get(`/api/v1/analyze/cohort/${clientId}`);
    return response.data;
};

export const getAttributionData = async (clientId: string): Promise<AttributionData[]> => {
    const response = await api.get(`/api/v1/analyze/attribution/${clientId}`);
    return response.data;
};

export const getSegmentData = async (clientId: string): Promise<SegmentRow[]> => {
    const response = await api.get(`/api/v1/analyze/segments/${clientId}`);
    return response.data;
};

// --- AI Assistant (Phase 6) ---
export const getAssistantQuickQueries = async (): Promise<Array<{ id: string; label: string; description: string }>> => {
    const response = await api.get('/api/v1/analyze/assistant/quick-queries');
    return response.data;
};

export const queryAssistant = async (query: string, clientId?: string): Promise<{ report: string; type: string }> => {
    const response = await api.post('/api/v1/analyze/assistant/query', {
        query,
        client_id: clientId || null,
    });
    return response.data;
};

// SSE 스트리밍 — EventSource 대신 fetch 기반 (Authorization 헤더 지원)
export const streamAssistantQuery = (
    query: string,
    clientId: string | undefined,
    sessionId: string | undefined,
    onDelta: (delta: string) => void,
    onDone: (sessionId: string) => void,
    onError: (err: string) => void,
): (() => void) => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || '';
    const ctrl = new AbortController();

    fetch(`${backendUrl}/api/v1/analyze/assistant/stream`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ query, client_id: clientId || null, session_id: sessionId || null }),
        signal: ctrl.signal,
    }).then(async (res) => {
        if (!res.ok || !res.body) {
            onError('스트리밍 연결 실패');
            return;
        }
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buf = '';
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buf += decoder.decode(value, { stream: true });
            const lines = buf.split('\n');
            buf = lines.pop() ?? '';
            for (const line of lines) {
                if (!line.startsWith('data: ')) continue;
                try {
                    const parsed = JSON.parse(line.slice(6));
                    if (parsed.done) {
                        onDone(parsed.session_id ?? '');
                    } else if (parsed.delta) {
                        onDelta(parsed.delta);
                    }
                } catch {}
            }
        }
    }).catch((err) => {
        if (err.name !== 'AbortError') onError(String(err));
    });

    return () => ctrl.abort();
};

export interface ChatSession {
    id: string;
    title: string | null;
    client_id: string | null;
    created_at: string;
    updated_at: string;
}

export interface ChatMessage {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    msg_type: string;
    created_at: string;
}

export const getChatSessions = async (): Promise<ChatSession[]> => {
    const response = await api.get('/api/v1/analyze/assistant/sessions');
    return response.data;
};

export const getChatSessionMessages = async (sessionId: string): Promise<{ session_id: string; title: string; messages: ChatMessage[] }> => {
    const response = await api.get(`/api/v1/analyze/assistant/sessions/${sessionId}/messages`);
    return response.data;
};

export const deleteChatSession = async (sessionId: string): Promise<void> => {
    await api.delete(`/api/v1/analyze/assistant/sessions/${sessionId}`);
};

// --- Auth & Users ---
export const login = async (email: string, password: string): Promise<{ access_token: string, user: User }> => {
    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);
    const response = await api.post('/api/v1/auth/login', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });

    // [FIX Issue #1] Store both access and refresh tokens
    const { access_token, refresh_token } = response.data;
    if (typeof window !== 'undefined') {
        localStorage.setItem('token', access_token);
        if (refresh_token) {
            localStorage.setItem('refreshToken', refresh_token);
        }
    }

    return response.data;
};

export const getUsers = async (): Promise<User[]> => {
    const response = await api.get('/api/v1/users/');
    return response.data;
};

export const createUser = async (user: UserCreate): Promise<User> => {
    const response = await api.post('/api/v1/users/', user);
    return response.data;
};

export const deleteUser = async (userId: string): Promise<{ status: string }> => {
    const response = await api.delete(`/api/v1/users/${userId}`);
    return response.data;
};

export const getSystemStatus = async (): Promise<{ status: string; workers: any; scheduler: boolean }> => {
    const response = await api.get('/api/v1/status/status');
    return response.data;
};

// --- Settlement APIs ---
export const getSettlements = async (clientId: string): Promise<Settlement[]> => {
    const response = await api.get(`/api/v1/settlement/${clientId}`);
    return response.data;
};

export const generateSettlement = async (clientId: string, year: number, month: number): Promise<Settlement> => {
    const response = await api.post(`/api/v1/settlement/generate`, null, {
        params: { client_id: clientId, year, month }
    });
    return response.data;
};

export const updateSettlementStatus = async (settlementId: string, status: string, notes?: string): Promise<Settlement> => {
    const response = await api.put(`/api/v1/settlement/${settlementId}/status`, { status, notes });
    return response.data;
};

// --- Efficiency Review APIs ---
export const getEfficiencyReview = async (clientId: string, days: number = 30): Promise<EfficiencyReview> => {
    const response = await api.get(`/api/v1/analyze/efficiency/${clientId}`, {
        params: { days }
    });
    return response.data;
};

// --- Search & History APIs (Onboarding Optimization) ---
export const searchClients = async (name: string): Promise<Client[]> => {
    const response = await api.get('/api/v1/clients/search', { params: { name } });
    return response.data;
};

export const searchTargets = async (name?: string): Promise<any[]> => {
    const response = await api.get('/api/v1/analyze/targets/search', { params: { name } });
    return response.data;
};

export const saveAnalysisHistory = async (data: { client_id: string, keyword: string, platform: string }): Promise<any> => {
    const response = await api.post('/api/v1/analyze/history', data);
    return response.data;
};

export const getAnalysisHistory = async (clientId: string): Promise<any[]> => {
    const response = await api.get(`/api/v1/analyze/history/${clientId}`);
    return response.data;
};

export const getScrapeResults = async (clientId: string, keyword?: string, platform: string = 'NAVER_PLACE'): Promise<any> => {
    const response = await api.get(`/api/v1/analyze/scrape-results/${clientId}`, {
        params: { keyword, platform }
    });
    return response.data;
};

// --- ROI / Ads APIs ---
export const getRoasTracking = async (clientId: string, days: number = 30): Promise<any> => {
    const response = await api.post('/api/v1/roi/track-roas', {
        client_id: clientId,
        days,
        // conversion_value 미전달 → 서버에서 클라이언트 DB 설정값 사용
    });
    return response.data;
};

export const getInefficientAds = async (clientId: string, days: number = 30): Promise<any> => {
    const response = await api.get(`/api/v1/roi/detect-inefficient/${clientId}`, {
        params: { days },
    });
    return response.data;
};

export const getBudgetReallocation = async (clientId: string, days: number = 30): Promise<any> => {
    const response = await api.get(`/api/v1/roi/budget-reallocation/${clientId}`, {
        params: { days },
    });
    return response.data;
};

// --- Lead Management APIs ---
export interface Lead {
    id: string;
    client_id: string;
    name: string | null;
    contact: string | null;
    channel: string | null;
    cohort_month: string;
    first_visit_date: string;
    created_at: string;
}

export interface LeadSummary {
    total_leads: number;
    new_this_month: number;
    total_conversions: number;
    total_revenue: number;
    conversion_rate: number;
    by_channel: Record<string, number>;
}

export interface LeadCreate {
    client_id: string;
    name?: string;
    contact?: string;
    channel?: string;
    first_visit_date?: string;
}

export const getLeadSummary = async (clientId: string): Promise<LeadSummary> => {
    const response = await api.get(`/api/v1/leads/summary/${clientId}`);
    return response.data;
};

export const getLeads = async (
    clientId: string,
    params?: { channel?: string; cohort_month?: string; limit?: number; offset?: number }
): Promise<Lead[]> => {
    const response = await api.get(`/api/v1/leads/${clientId}`, { params });
    return response.data;
};

export const createLead = async (data: LeadCreate): Promise<Lead> => {
    const response = await api.post('/api/v1/leads/', data);
    return response.data;
};

export const deleteLead = async (leadId: string): Promise<void> => {
    await api.delete(`/api/v1/leads/${leadId}`);
};

export const getCohortAnalysis = async (clientId: string): Promise<any[]> => {
    const response = await api.get(`/api/v1/leads/cohort/${clientId}`);
    return response.data;
};

// --- Competitor Intelligence APIs ---

export interface CompetitorDiscoveryItem {
    target_id: string;
    name: string;
    type: string;
    overlap_score: number;
    shared_keywords: number;
    total_keywords: number;
    keywords_appeared: number;
    shared_keyword_terms: string[];
}

export interface CompetitorDiscoveryResult {
    status: string;
    count: number;
    competitors: CompetitorDiscoveryItem[];
    parameters: {
        client_id: string;
        platform: string;
        threshold: number;
        days: number;
    };
}

export const discoverCompetitors = async (params: {
    client_id: string;
    platform?: string;
    keyword_overlap_threshold?: number;
    min_appearances?: number;
    top_n?: number;
    days?: number;
}): Promise<CompetitorDiscoveryResult> => {
    const response = await api.post('/api/v1/competitors/discover', params);
    return response.data;
};

export interface RankingDropAlert {
    keyword_id: string;
    keyword: string;
    previous_rank: number;
    current_rank: number;
    drop: number;
}

export interface RankingDropResult {
    status: string;
    alerts_created: number;
    drops: RankingDropAlert[];
}

export const createRankingDropAlert = async (
    clientId: string,
    threshold: number = 5
): Promise<RankingDropResult> => {
    const response = await api.post(
        `/api/v1/trends/alerts/ranking-drop/${clientId}`,
        null,
        { params: { rank_drop_threshold: threshold } }
    );
    return response.data;
};

export interface SearchTrendPrediction {
    trend_data: { date: string; appearances: number; avg_rank: number }[];
    recent_avg: number;
    overall_avg: number;
    prediction: string;
}

export interface SearchTrendsResult {
    analysis_period: string;
    predictions: Record<string, SearchTrendPrediction>;
}

export const predictSearchTrends = async (
    clientId: string,
    days: number = 90
): Promise<{ status: string; data: SearchTrendsResult }> => {
    const response = await api.get(`/api/v1/trends/predict-search-trends/${clientId}`, {
        params: { days }
    });
    return response.data;
};

// --- Competitor Strategy Analysis ---

export interface StrategyTopKeyword {
    term: string;
    appearances: number;
    avg_rank: number;
    best_rank: number;
}

export interface StrategyRankTrendPoint {
    date: string;
    avg_rank: number;
}

export interface CompetitorStrategyAnalysis {
    target_id: string;
    target_name: string;
    platform: string;
    analysis_period: string;
    top_keywords: StrategyTopKeyword[];
    activity_by_hour: Record<string, number>;
    activity_by_dow: Record<string, number>;
    rank_trend: StrategyRankTrendPoint[];
    trend_direction: string;
}

export const analyzeCompetitorStrategy = async (params: {
    target_id: string;
    platform?: string;
    days?: number;
}): Promise<{ status: string; analysis: CompetitorStrategyAnalysis }> => {
    const response = await api.post('/api/v1/competitors/strategy-analysis', params);
    return response.data;
};

// --- Notification Types ---

export interface Notification {
    id: string;
    title: string;
    content?: string;
    link?: string;
    is_read: boolean;
    type?: string;
    created_at: string;
}

export default api;
