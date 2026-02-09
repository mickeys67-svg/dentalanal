export interface MissionTelemetry {
    mission_id: string;
    stage: string;
    timestamp: string;
    message?: string;
}

export interface CompetitorData {
    name: string;
    rank_count: number;
    avg_rank: number;
    share: number;
}

export interface SOVDataItem {
    date: string;
    sov: number;
    rank_1_10: number;
}

export interface ScrapeResponse {
    task_id: string;
    message: string;
}
