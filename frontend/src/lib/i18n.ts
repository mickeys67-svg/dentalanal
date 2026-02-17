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

export const UI_TEXT = {
    RANKING: {
        TITLE: '키워드 순위 추적',
        SUBTITLE: '네이버 플레이스 상위 노출 순위와 경쟁사 현황을 실시간으로 분석합니다.',
        SEARCH_LABEL: '분석할 키워드',
        SEARCH_PLACEHOLDER: '예: 강남역 치과, 임플란트 잘하는 곳',
        BUTTON_SEARCH: '조사',
        BUTTON_LOADING: '조사 중...',
        INFO_TITLE: 'Info',
        INFO_TEXT: '실시간 데이터는 네이버 검색 결과를 기반으로 하며, 지역 및 개인화 설정에 따라 실제 결과와 1~2위 정도 차이가 있을 수 있습니다.',
    },
    SUMMARY: {
        TOP3: '상위 노출 (Top 3)',
        AVG_RANK: '평균 순위',
        TOTAL_KEYWORDS: '추적 키워드',
        COMPETITORS: '경쟁 강도',
        UNIT_RANK: '위',
        UNIT_COUNT: '개',
        UNIT_PERCENT: '%',
        COMPETITOR_SHARE: '점유율',
        DESC_TOP3: '전체 키워드 중',
        DESC_AVG: '전체 키워드 평균',
        DESC_TOTAL: '등록된 키워드 수',
        DESC_COMPETITOR: '1위 경쟁사',
        LOADING: '분석 중...',
    },
    TABLE: {
        TITLE_SUFFIX: '검색 결과',
        SUBTITLE: '실시간 네이버 플레이스 노출 순위',
        UPDATE_TIME: '업데이트',
        HEADER_RANK: '순위',
        HEADER_NAME: '업체명 (Title)',
        HEADER_CATEGORY: '카테고리',
        HEADER_CHANGE: '변동',
        HEADER_LINK: '링크',
        EMPTY_TITLE: '데이터가 없습니다',
        EMPTY_DESC: '키워드를 입력하고 조사를 시작하여 순위를 추적하세요.',
        LOADING_TITLE: '순위 데이터를 불러오는 중...',
        PREMIUM_RANK: 'Premium Rank',
        VISIT_LINK: '방문',
        PLACEHOLDER_BLOG: '플레이스',
    },
    COMPETITOR: {
        TITLE: '상위 노출 경쟁사 분석',
        LOADING: '경쟁사 분석 중...',
        NO_DATA: '데이터 없음',
        CHART_LABEL: '노출 횟수',
        LIST_TITLE: '상세 점유율 현황',
        SHARE: '점유율',
        AVG: '평균',
    },
    VIRAL: {
        TITLE: '바이럴 모니터링',
        SUBTITLE: '네이버 블로그/카페 등 커뮤니티 언급을 실시간으로 추적합니다.',
        SEARCH_LABEL: '모니터링 키워드',
        SEARCH_PLACEHOLDER: '예: 강남역 치과 후기',
        FEED_TITLE: '최신 언급 피드',
        SENTIMENT_TITLE: '언급 감성 분석 (AI Beta)',
        POSITIVE: '긍정',
        NEGATIVE: '부정',
        NEUTRAL: '중립',
        LOADING: '바이럴 데이터를 분석 중...',
        EMPTY_DESC: '키워드를 입력하여 커뮤니티 반응을 확인하세요.',
        VIEW_ORIGINAL: '원문 보기',
        DATE_FORMAT: 'yyyy-MM-dd',
        SOURCE_BLOG: '블로그',
        SOURCE_CAFE: '카페',
    }
};
