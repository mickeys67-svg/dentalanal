"""
경쟁사 발굴 알고리즘 단위 테스트
- DB 의존성 없는 순수 로직만 테스트
"""
import pytest
from app.core.algorithms.overlap import (
    jaccard_similarity,
    rank_competitors,
    predict_trend_direction,
)


class TestJaccardSimilarity:
    def test_identical_sets(self):
        s = {"a", "b", "c"}
        assert jaccard_similarity(s, s) == 1.0

    def test_disjoint_sets(self):
        assert jaccard_similarity({"a", "b"}, {"c", "d"}) == 0.0

    def test_partial_overlap(self):
        # A={1,2,3}, B={2,3,4} → intersection=2, union=4 → 0.5
        result = jaccard_similarity({1, 2, 3}, {2, 3, 4})
        assert result == pytest.approx(0.5)

    def test_empty_sets(self):
        assert jaccard_similarity(set(), set()) == 0.0

    def test_one_empty_set(self):
        assert jaccard_similarity({"a"}, set()) == 0.0

    def test_subset(self):
        # A⊂B → J = |A| / |B|
        result = jaccard_similarity({1, 2}, {1, 2, 3, 4})
        assert result == pytest.approx(0.5)

    def test_score_range(self):
        score = jaccard_similarity({1, 2, 3, 4}, {3, 4, 5})
        assert 0.0 <= score <= 1.0


class TestRankCompetitors:
    def test_basic_ranking(self):
        client_kws = {1, 2, 3, 4, 5}
        targets = {
            "t1": {1, 2, 3, 4, 5},      # overlap=1.0
            "t2": {1, 2, 3},             # overlap=3/5=0.6
            "t3": {6, 7, 8},             # overlap=0.0 → 제외
        }
        results = rank_competitors(client_kws, targets, threshold=0.3, min_appearances=1)
        assert len(results) == 2
        assert results[0]["target_id"] == "t1"
        assert results[1]["target_id"] == "t2"

    def test_threshold_filtering(self):
        client_kws = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10}
        targets = {
            "t1": {1, 2},   # overlap=2/10=0.2 → 0.3 임계값에 미달
            "t2": {1, 2, 3, 4},  # overlap=4/10=0.4 → 통과
        }
        results = rank_competitors(client_kws, targets, threshold=0.3, min_appearances=1)
        assert len(results) == 1
        assert results[0]["target_id"] == "t2"

    def test_min_appearances_filtering(self):
        client_kws = {1, 2, 3, 4, 5}
        targets = {
            "t1": {1, 2},        # 2개 → min_appearances=3 미달
            "t2": {1, 2, 3},     # 3개 → 통과
        }
        results = rank_competitors(
            client_kws, targets, threshold=0.0, min_appearances=3
        )
        assert len(results) == 1
        assert results[0]["target_id"] == "t2"

    def test_top_n_limit(self):
        client_kws = {1, 2, 3, 4, 5}
        targets = {f"t{i}": {1, 2, 3} for i in range(10)}
        results = rank_competitors(client_kws, targets, threshold=0.0, min_appearances=1, top_n=3)
        assert len(results) == 3

    def test_empty_target_map(self):
        results = rank_competitors({1, 2, 3}, {}, threshold=0.3, min_appearances=1)
        assert results == []

    def test_sorted_descending(self):
        client_kws = {1, 2, 3, 4, 5}
        targets = {
            "low":  {1},            # overlap=1/5=0.2 → 제외(threshold=0.3)
            "mid":  {1, 2, 3},      # overlap=3/5=0.6
            "high": {1, 2, 3, 4},   # overlap=4/5=0.8
        }
        results = rank_competitors(client_kws, targets, threshold=0.3, min_appearances=1)
        scores = [r["overlap_score"] for r in results]
        assert scores == sorted(scores, reverse=True)


class TestPredictTrendDirection:
    def test_rising_trend(self):
        # 최근 7일 평균이 전체 평균의 1.2배 초과
        data = [10] * 10 + [25] * 7   # 전체평균 ≈ 16.2, 최근7일=25 → 1.54배
        assert predict_trend_direction(data) == "상승 추세"

    def test_dropping_trend(self):
        # 최근 7일 평균이 전체 평균의 0.8배 미만
        data = [20] * 10 + [5] * 7    # 전체평균 ≈ 14.6, 최근7일=5 → 0.34배
        assert predict_trend_direction(data) == "하락 추세"

    def test_stable_trend(self):
        data = [10] * 17
        assert predict_trend_direction(data) == "안정 추세"

    def test_insufficient_data(self):
        assert predict_trend_direction([1, 2, 3], window=7) == "데이터 부족"
        assert predict_trend_direction([], window=7) == "데이터 부족"

    def test_exactly_window_size(self):
        data = [10] * 7
        result = predict_trend_direction(data, window=7)
        assert result in ("안정 추세", "상승 추세", "하락 추세")

    def test_zero_overall_avg(self):
        data = [0] * 10
        assert predict_trend_direction(data) == "데이터 부족"

    def test_custom_thresholds(self):
        # data=[10]*10+[15]*7 → 전체평균≈12.06, 최근7일=15, 비율≈1.244
        # 기본 임계값(1.2) 초과 → 상승 추세
        data = [10] * 10 + [15] * 7
        assert predict_trend_direction(data, rise_threshold=1.2) == "상승 추세"
        # rise_threshold를 1.3으로 높이면 1.244 < 1.3 → 안정 추세
        assert predict_trend_direction(data, rise_threshold=1.3) == "안정 추세"
