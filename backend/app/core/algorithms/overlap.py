"""
키워드 중복도 알고리즘 (DB 의존성 없는 순수 로직)
"""
from typing import Set, Dict, List, Any
import statistics


def jaccard_similarity(set_a: Set, set_b: Set) -> float:
    """
    Jaccard 유사도 계산: |A ∩ B| / |A ∪ B|

    Args:
        set_a: 집합 A
        set_b: 집합 B

    Returns:
        0.0 ~ 1.0 사이의 유사도 (두 집합이 모두 비어 있으면 0.0)
    """
    union = set_a | set_b
    if not union:
        return 0.0
    intersection = set_a & set_b
    return len(intersection) / len(union)


def rank_competitors(
    client_keyword_set: Set,
    target_keyword_map: Dict[str, Set],
    threshold: float = 0.3,
    min_appearances: int = 3,
    top_n: int = 10,
) -> List[Dict[str, Any]]:
    """
    경쟁사 랭킹 계산 (DB 쿼리 결과를 받아 순수 연산만 담당)

    Args:
        client_keyword_set: 클라이언트의 키워드 ID 집합
        target_keyword_map: {target_id: 해당 타겟이 등장한 키워드 ID 집합}
        threshold: Jaccard 유사도 임계값
        min_appearances: 최소 등장 키워드 수
        top_n: 반환할 최대 경쟁사 수

    Returns:
        [{"target_id": str, "overlap_score": float, "shared": int, "total": int}, ...]
    """
    results = []

    for target_id, target_kw_set in target_keyword_map.items():
        if len(target_kw_set) < min_appearances:
            continue

        score = jaccard_similarity(client_keyword_set, target_kw_set)

        if score >= threshold:
            intersection = client_keyword_set & target_kw_set
            union = client_keyword_set | target_kw_set
            results.append({
                "target_id": target_id,
                "overlap_score": round(score, 3),
                "shared": len(intersection),
                "total": len(union),
            })

    results.sort(key=lambda x: x["overlap_score"], reverse=True)
    return results[:top_n]


def predict_trend_direction(
    appearances: List[int],
    window: int = 7,
    rise_threshold: float = 1.2,
    drop_threshold: float = 0.8,
) -> str:
    """
    Simple Moving Average 기반 트렌드 방향 예측

    Args:
        appearances: 시간순 등장 횟수 리스트
        window: 최근 N일 창
        rise_threshold: 상승 판단 비율 (최근 평균 / 전체 평균)
        drop_threshold: 하락 판단 비율

    Returns:
        "상승 추세" | "하락 추세" | "안정 추세" | "데이터 부족"
    """
    if len(appearances) < window:
        return "데이터 부족"

    recent_avg = statistics.mean(appearances[-window:])
    overall_avg = statistics.mean(appearances)

    if overall_avg == 0:
        return "데이터 부족"

    ratio = recent_avg / overall_avg

    if ratio > rise_threshold:
        return "상승 추세"
    elif ratio < drop_threshold:
        return "하락 추세"
    else:
        return "안정 추세"
