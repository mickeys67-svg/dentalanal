export const METRIC_LABELS: Record<string, string> = {
    // Basic Metrics
    'impressions': '노출수',
    'clicks': '클릭수',
    'conversions': '전환수',
    'spend': '광고비',
    'ctr': '클릭률',
    'cpc': '클릭당비용',
    'roas': 'ROAS',
    'cost': '비용',
    'reach': '도달수',
    'frequency': '빈도',

    // Status
    'ACTIVE': '활성',
    'PAUSED': '일시중지',
    'COMPLETED': '완료',
    'ERROR': '오류',

    // Platforms
    'NAVER': '네이버',
    'GOOGLE': '구글',
    'META': '메타',
    'KAKAO': '카카오',

    // KPI Titles
    'Total Spend': '총 광고 집행비',
    'Total Conversions': '총 전환수',
    'Average ROAS': '평균 ROAS',
    'Total Clicks': '총 클릭수'
};

export const translateMetric = (key: string): string => {
    return METRIC_LABELS[key] || METRIC_LABELS[key.toLowerCase()] || key;
};

export const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('ko-KR', {
        style: 'currency',
        currency: 'KRW',
    }).format(value);
};

export const formatPercent = (value: number) => {
    return `${value.toFixed(2)}%`;
};
