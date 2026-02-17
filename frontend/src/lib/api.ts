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

// Add a response interceptor to handle 401 Unauthorized globally
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
                localStorage.removeItem('token');
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

// --- Auth & Users ---
export const login = async (email: string, password: string): Promise<{ access_token: string, user: User }> => {
    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);
    const response = await api.post('/api/v1/auth/login', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
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

export default api;
