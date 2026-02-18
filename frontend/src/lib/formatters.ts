/**
 * 날짜/시간 포맷 유틸
 */

export function timeAgo(dateStr: string): string {
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return "방금 전";
    if (mins < 60) return `${mins}분 전`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}시간 전`;
    const days = Math.floor(hours / 24);
    return `${days}일 전`;
}

/**
 * 순위 변화 심각도 계산
 * @param drop 순위 하락폭 (양수 = 하락)
 */
export function getRankDropSeverity(drop: number): "high" | "medium" | "low" {
    if (drop >= 10) return "high";
    if (drop >= 5) return "medium";
    return "low";
}

/**
 * Jaccard 유사도 계산 (프론트엔드 표시용)
 * @param score 0~1 사이 overlap_score
 */
export function getOverlapLevel(score: number): "danger" | "warning" | "low" {
    if (score >= 0.7) return "danger";
    if (score >= 0.4) return "warning";
    return "low";
}

/**
 * 숫자를 한국식 통화 형식으로 포맷
 */
export function formatKRW(amount: number): string {
    if (amount >= 100_000_000) {
        return `${(amount / 100_000_000).toFixed(1)}억원`;
    }
    if (amount >= 10_000) {
        return `${(amount / 10_000).toFixed(0)}만원`;
    }
    return `${amount.toLocaleString()}원`;
}
