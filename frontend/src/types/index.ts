export type PlatformType = 'NAVER_VIEW' | 'NAVER_PLACE' | 'NAVER_AD' | 'GOOGLE_ADS' | 'META_ADS' | 'KAKAO_AD';

export interface KPI {
    id: string;
    label: string;
    value: string | number;
    change: number;
    trend: 'up' | 'down' | 'neutral';
    color?: string;
}

export interface DashboardKPI {
    title: string;
    value: string | number;
    change: number;
    prefix?: string;
    suffix?: string;
}

export interface Campaign {
    id: string;
    name: string;
    status: 'ACTIVE' | 'PAUSED' | 'COMPLETED' | 'ERROR';
    platform: PlatformType | string;
    budget: number;
    spend: number;
    impressions: number;
    clicks: number;
    conversions: number;
    ctr: number;
    cpc: number;
    roas: number;
}

export interface FunnelStage {
    stage: string;
    value: number;
}

export interface CohortRow {
    month: string;
    size: number;
    retention: number[];
}

export interface AttributionData {
    channel: string;
    first_touch: number;
    last_touch: number;
    linear: number;
}

export interface SegmentRow {
    segment: string;
    visitors: number;
    conversion_rate: number;
    roas: number;
}

export interface SWOTData {
    strengths: string[];
    weaknesses: string[];
    opportunities: string[];
    threats: string[];
}

export interface StrategyGoal {
    id: string;
    title: string;
    description?: string;
    smart_s?: string;
    smart_m?: string;
    smart_a?: string;
    smart_r?: string;
    smart_t?: string;
    status: 'IN_PROGRESS' | 'COMPLETED' | 'ABANDONED';
}

export interface CollaborativeTask {
    id: string;
    title: string;
    status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED';
    owner: string;
    deadline?: string;
}

export interface ApprovalRequest {
    id: string;
    title: string;
    description?: string;
    status: 'PENDING' | 'APPROVED' | 'REJECTED';
    request_type: string;
    due_date?: string;
}

export interface Connector {
    id: string;
    name: string;
    description: string;
    category: string;
    status: 'AVAILABLE' | 'UNAVAILABLE' | 'COMING_SOON';
}

export interface KeywordRank {
    rank: number;
    title: string;
    blog_name?: string;
    link?: string;
    created_at: string;
}
export interface SOVAnalysisResult {
    keyword: string;
    total_items: number;
    target_hits: number;
    sov_score: number;
    top_rank?: number;
}

export interface CompetitorAnalysisResult {
    keyword: string;
    platform: string;
    top_n: number;
    competitors: {
        name: string;
        rank_count: number;
        avg_rank: number;
        share: number;
    }[];
}

export interface Client {
    id: string;
    agency_id: string;
    name: string;
    industry: string;
}

export interface PlatformConnection {
    id: string;
    platform: PlatformType;
    status: 'ACTIVE' | 'INACTIVE' | 'ERROR';
    created_at: string;
}

export enum UserRole {
    SUPER_ADMIN = 'SUPER_ADMIN',
    ADMIN = 'ADMIN',
    EDITOR = 'EDITOR',
    VIEWER = 'VIEWER',
}

export interface User {
    id: string;
    email: string;
    name: string;
    role: UserRole;
    cnt: string;
    is_active: number;
    agency_id?: string;
    social_provider?: string;
    created_at?: string;
}

export interface UserCreate {
    email: string;
    password: string;
    name?: string;
    role?: UserRole; // Optional because backend defaults to VIEWER
    birth_date?: string;
    agency_id?: string;
}

// --- Efficiency & Analysis ---
export interface EfficiencyItem {
    name: string;
    spend: number;
    conversions: number;
    clicks: number;
    impressions: number;
    roas: number;
    cpa: number;
    ctr: number;
    cvr: number;
    suggestion?: string;
}

export interface EfficiencyReview {
    items: EfficiencyItem[];
    overall_roas: number;
    total_spend: number;
    total_conversions: number;
    ai_review: string;
    period: string;
}

// --- Settlement ---
export interface Settlement {
    id: string;
    client_id: string;
    period: string;
    total_spend: number;
    fee_amount: number;
    tax_amount: number;
    total_amount: number;
    status: 'PENDING' | 'REQUESTED' | 'PAID' | 'CANCELLED';
    notes?: string;
    due_date?: string;
    issued_at?: string;
    paid_at?: string;
    created_at: string;
    updated_at: string;
}

// --- Reports ---
export interface ReportWidget {
    id: string;
    type: 'KPI' | 'CHART' | 'TABLE' | 'SOV' | 'COMPETITORS' | 'RANKINGS';
    title: string;
    config: Record<string, any>;
    data?: any;
}

export interface ReportTemplate {
    id: string;
    name: string;
    description?: string;
    config: {
        widgets: ReportWidget[];
    };
    created_at: string;
}

export interface Report {
    id: string;
    client_id: string;
    template_id: string;
    title: string;
    status: 'PENDING' | 'COMPLETED' | 'ERROR';
    data: {
        widgets: ReportWidget[];
    };
    created_at: string;
}
