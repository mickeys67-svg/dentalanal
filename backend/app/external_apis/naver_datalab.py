"""
Naver DataLab - 통합검색어 트렌드 API (검색어트렌드)
공식 문서: https://developers.naver.com/docs/serviceapi/datalab/search/search.md

⚠️ 중요 (가짜 데이터 금지 원칙 직결):
  DataLab 은 **절대 검색량이 아니라 상대지수**를 반환합니다.
  - 각 응답은 해당 요청 기간 내 최댓값을 100으로 정규화한 0~100 비율(ratio).
  - 따라서 서로 다른 호출(예: 성별 m 호출 vs f 호출)의 값은 각각
    독립 정규화되어 "직접 비율 비교"가 엄밀히는 성립하지 않습니다.
  - 본 모듈은 이를 절대량으로 위장하지 않고 "상대지수"로 그대로 노출합니다.

인증: naver_search.py 와 동일 (X-Naver-Client-Id / X-Naver-Client-Secret).
자격증명: NAVER_CLIENT_ID / NAVER_CLIENT_SECRET
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# 데모그래픽 조회 시 동시 호출 상한 (초당 레이트리밋 회피 + 순차 대비 지연 단축)
DEMO_CONCURRENCY = 3

DATALAB_URL = "https://openapi.naver.com/v1/datalab/search"
MAX_GROUPS = 5  # 데이터랩은 keywordGroups 최대 5개

# 네이버 데이터랩 연령대 코드 → 라벨 (공식 매핑)
AGE_BANDS: Dict[str, str] = {
    "1": "0-12",
    "2": "13-18",
    "3": "19-24",
    "4": "25-29",
    "5": "30-34",
    "6": "35-39",
    "7": "40-44",
    "8": "45-49",
    "9": "50-54",
    "10": "55-59",
    "11": "60+",
}

GENDERS: Dict[str, str] = {"m": "남성", "f": "여성"}


class NaverDataLabClient:
    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None):
        self.client_id = client_id or settings.NAVER_CLIENT_ID
        self.client_secret = client_secret or settings.NAVER_CLIENT_SECRET

    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret)

    @property
    def _headers(self) -> Dict[str, str]:
        return {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret,
            "Content-Type": "application/json",
        }

    async def _post(self, body: Dict[str, Any], max_retries: int = 3) -> Dict[str, Any]:
        """DataLab POST. 429(레이트리밋)는 지수 백오프로 재시도 (naver_search.py 선례와 동일)."""
        async with httpx.AsyncClient(timeout=15) as client:
            for attempt in range(max_retries + 1):
                resp = await client.post(DATALAB_URL, headers=self._headers, json=body)
                if resp.status_code == 429 and attempt < max_retries:
                    sleep_s = 1.0 * (2 ** attempt)
                    logger.warning(
                        f"[DataLab] 429 rate limit, {sleep_s}s 후 재시도 ({attempt+1}/{max_retries})"
                    )
                    await asyncio.sleep(sleep_s)
                    continue
                if resp.status_code != 200:
                    logger.error(f"[DataLab] API error {resp.status_code}: {resp.text[:300]}")
                    resp.raise_for_status()
                return resp.json()
        # 도달 불가(마지막 시도는 위에서 return/raise) — 방어적 반환
        raise httpx.HTTPError("[DataLab] 재시도 소진")

    async def search_trend(
        self,
        keyword_groups: List[Dict[str, Any]],
        start_date: str,
        end_date: str,
        time_unit: str = "date",  # date | week | month
        device: str = "",  # "" | pc | mo
        gender: str = "",  # "" | m | f
        ages: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        검색어 트렌드 조회. 반환은 상대지수(0~100) 시계열.
        keyword_groups: [{"groupName": "다이어트", "keywords": ["다이어트", "다이어트약"]}]
        """
        if not self.is_configured():
            raise ValueError("NAVER_CLIENT_ID / NAVER_CLIENT_SECRET 미설정 (데이터랩 API 사용 불가).")

        if len(keyword_groups) > MAX_GROUPS:
            keyword_groups = keyword_groups[:MAX_GROUPS]
            logger.warning(f"[DataLab] keywordGroups 최대 {MAX_GROUPS}개로 잘림")

        body: Dict[str, Any] = {
            "startDate": start_date,
            "endDate": end_date,
            "timeUnit": time_unit,
            "keywordGroups": keyword_groups,
        }
        if device:
            body["device"] = device
        if gender:
            body["gender"] = gender
        if ages:
            body["ages"] = ages

        return await self._post(body)

    async def get_trend_series(
        self,
        keywords: List[str],
        start_date: str,
        end_date: str,
        time_unit: str = "date",
        device: str = "",
        gender: str = "",
        ages: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        키워드 리스트를 각각 단일 그룹으로 트렌드 조회.
        반환: [{"keyword": ..., "series": [{"period","ratio"}, ...]}]  (상대지수)
        """
        groups = [{"groupName": k, "keywords": [k]} for k in keywords if k.strip()][:MAX_GROUPS]
        if not groups:
            return []
        raw = await self.search_trend(
            groups, start_date, end_date, time_unit, device, gender, ages
        )
        out = []
        for r in raw.get("results", []):
            out.append(
                {
                    "keyword": r.get("title"),
                    "series": [
                        {"period": p.get("period"), "ratio": p.get("ratio")}
                        for p in r.get("data", [])
                    ],
                }
            )
        return out

    async def get_demographics(
        self,
        keyword: str,
        start_date: str,
        end_date: str,
    ) -> Dict[str, Any]:
        """
        단일 키워드의 성별/연령대 상대 관심도.

        ⚠️ 성별·연령대 각 세그먼트는 데이터랩 개별 호출(각각 독립 정규화)이므로
        엄밀한 "인구 비율"이 아니라 **상대 관심도 지수**입니다. 그대로 라벨링해 반환.
        각 세그먼트 지수 = 해당 세그먼트 필터 응답의 ratio 평균(기간 평균).

        ⚠️ 성별 2 + 연령 11 = 13회 개별 호출이 필요(데이터랩은 요청당 세그먼트 필터 1개).
        레이트리밋/지연 완화를 위해 제한된 동시성(DEMO_CONCURRENCY)으로 실행하고,
        각 세그먼트의 호출 실패(429 등)를 진짜 "데이터 없음"과 구분해 failed 플래그로 노출한다.
        (가짜 데이터 금지: 인프라 실패를 0/무관심으로 위장하지 않음)

        반환:
          {
            "keyword": ...,
            "gender": [{"segment":"남성","index":..,"failed":false}, ...],
            "age":    [{"segment":"19-24","index":..,"failed":false}, ...],
            "partial": bool,   # 일부 세그먼트 조회 실패 여부
            "note": "상대 관심도 지수(0~100). 인구 비율 아님."
          }
        """
        group = [{"groupName": keyword, "keywords": [keyword]}]
        sem = asyncio.Semaphore(DEMO_CONCURRENCY)

        async def _seg(gender: str = "", ages=None) -> Dict[str, Any]:
            """반환 {index: float|None, failed: bool}. failed=True → 호출 실패(데이터없음 아님)."""
            async with sem:
                try:
                    raw = await self.search_trend(
                        group, start_date, end_date, "month", gender=gender, ages=ages
                    )
                except Exception as e:
                    logger.warning(f"[DataLab] demographics 호출 실패 g={gender} a={ages}: {e}")
                    return {"index": None, "failed": True}
            data = (raw.get("results") or [{}])[0].get("data", [])
            ratios = [d.get("ratio") for d in data if isinstance(d.get("ratio"), (int, float))]
            if not ratios:
                return {"index": None, "failed": False}  # 진짜 데이터 없음
            return {"index": round(sum(ratios) / len(ratios), 2), "failed": False}

        gender_codes = list(GENDERS.items())
        age_codes = list(AGE_BANDS.items())
        # 성별 + 연령 세그먼트를 제한 동시성으로 병렬 실행
        results = await asyncio.gather(
            *[_seg(gender=code) for code, _ in gender_codes],
            *[_seg(ages=[code]) for code, _ in age_codes],
        )
        gender_res = results[: len(gender_codes)]
        age_res = results[len(gender_codes):]

        gender_out = [
            {"segment": label, "index": r["index"], "failed": r["failed"]}
            for (_, label), r in zip(gender_codes, gender_res)
        ]
        age_out = [
            {"segment": label, "index": r["index"], "failed": r["failed"]}
            for (_, label), r in zip(age_codes, age_res)
        ]
        partial = any(r["failed"] for r in results)

        return {
            "keyword": keyword,
            "gender": gender_out,
            "age": age_out,
            "partial": partial,
            "note": "상대 관심도 지수(0~100). 절대 인구 비율이 아님 (네이버 데이터랩 정규화 특성).",
        }
