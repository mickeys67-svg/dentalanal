"""
Naver Search Ad - Keyword Tool API (키워드도구)
공식 문서: https://naver.github.io/searchad-apidoc/#/tags/RelKwdStat

제공 데이터 (모두 direct-real, 네이버 공식 API 실측값):
  - 월간 검색수 (PC / 모바일)
  - 월평균 클릭수 / 클릭률 (PC / 모바일)
  - 경쟁정도 (compIdx: 높음/중간/낮음)
  - 연관키워드 (relKeyword)

인증: NaverAdsService 와 동일한 HMAC-SHA256 서명 방식.
자격증명: NAVER_AD_CUSTOMER_ID / NAVER_AD_ACCESS_LICENSE / NAVER_AD_SECRET_KEY
"""
import time
import hmac
import hashlib
import base64
import logging
from typing import List, Dict, Any, Optional, Tuple

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# 키워드도구는 한 번에 최대 5개의 hintKeywords 를 허용합니다.
MAX_HINTS_PER_CALL = 5


def _parse_count(value: Any) -> Tuple[Optional[int], bool]:
    """
    월간 검색수 필드 파싱.  반환: (검색수 int 또는 None, masked)

    ⚠️ 가짜 데이터 금지 원칙:
      네이버는 검색수가 10 미만이면 실제 정수 대신 마스킹 문자열 "< 10" 을 반환한다
      (정확값 비공개). 이를 임의 상수로 치환하면 실측값과 구분 불가능해지고
      실제 3·8인 키워드가 동일 수치로 표시되어 사기가 된다. 따라서:
        - 정상 정수                 → (int, False)
        - "< 10" (마스킹, 실측불가)  → (None, True)   # 값 없음 + 마스킹 플래그
        - None/파싱불가/NaN/inf      → (None, False)
      호출측은 masked=True 를 받아 "10 미만"으로 정성 강등해 표기해야 한다.
    """
    if value is None or isinstance(value, bool):
        return None, False
    if isinstance(value, (int, float)):
        try:
            return int(value), False
        except (ValueError, OverflowError):  # NaN, inf 방어
            return None, False
    s = str(value).strip()
    if s.startswith("<"):
        return None, True  # "< 10": 10 미만, 실측값 없음
    try:
        return int(s.replace(",", "")), False
    except ValueError:
        return None, False


class NaverKeywordToolClient:
    BASE_URL = "https://api.searchad.naver.com"
    PATH = "/keywordstool"

    def __init__(
        self,
        customer_id: Optional[str] = None,
        access_license: Optional[str] = None,
        secret_key: Optional[str] = None,
    ):
        self.customer_id = customer_id or settings.NAVER_AD_CUSTOMER_ID
        self.access_license = access_license or settings.NAVER_AD_ACCESS_LICENSE
        self.secret_key = secret_key or settings.NAVER_AD_SECRET_KEY

    def is_configured(self) -> bool:
        return bool(self.customer_id and self.access_license and self.secret_key)

    def _headers(self, method: str, path: str) -> Dict[str, str]:
        timestamp = str(int(time.time() * 1000))
        message = f"{timestamp}.{method}.{path}"
        signature = base64.b64encode(
            hmac.new(
                self.secret_key.encode("utf-8"),
                message.encode("utf-8"),
                hashlib.sha256,
            ).digest()
        ).decode("utf-8")
        return {
            "X-Timestamp": timestamp,
            "X-API-KEY": self.access_license,
            "X-Customer": str(self.customer_id),
            "X-Signature": signature,
        }

    async def _fetch_raw(self, hint_keywords: List[str]) -> List[Dict[str, Any]]:
        """최대 5개 힌트 키워드에 대한 원시 keywordList 반환."""
        # 네이버 키워드도구는 공백 포함 키워드를 허용하지 않으므로 공백 제거.
        cleaned = [k.replace(" ", "") for k in hint_keywords if k.strip()]
        if not cleaned:
            return []

        params = {
            "hintKeywords": ",".join(cleaned),
            "showDetail": "1",
        }
        headers = self._headers("GET", self.PATH)

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                self.BASE_URL + self.PATH, headers=headers, params=params
            )
            if resp.status_code != 200:
                logger.error(
                    f"[KeywordTool] API error {resp.status_code}: {resp.text[:300]}"
                )
                resp.raise_for_status()
            data = resp.json()
        return data.get("keywordList", []) or []

    @staticmethod
    def _normalize_row(row: Dict[str, Any]) -> Dict[str, Any]:
        pc, pc_masked = _parse_count(row.get("monthlyPcQcCnt"))
        mobile, mobile_masked = _parse_count(row.get("monthlyMobileQcCnt"))
        masked = pc_masked or mobile_masked
        pc_clk, _ = _parse_count(row.get("monthlyAvePcClkCnt"))
        mobile_clk, _ = _parse_count(row.get("monthlyAveMobileClkCnt"))
        # 합계: 둘 다 마스킹(값 없음)이면 실측 총계 없음(None).
        # 하나만 알려지면 알려진 값 합(=하한). masked 플래그로 "10 미만 포함" 표기.
        if pc is None and mobile is None:
            total: Optional[int] = None
        else:
            total = (pc or 0) + (mobile or 0)
        return {
            "keyword": row.get("relKeyword", ""),
            "monthly_pc": pc,
            "monthly_mobile": mobile,
            "monthly_total": total,
            "monthly_masked": masked,  # True → "10 미만" 구간 포함(실측 아님)
            "monthly_avg_pc_clicks": pc_clk,
            "monthly_avg_mobile_clicks": mobile_clk,
            "comp_idx": row.get("compIdx"),  # "높음"/"중간"/"낮음"
        }

    async def get_keyword_stats(
        self, keywords: List[str], related_limit: int = 20
    ) -> Dict[str, Any]:
        """
        입력 키워드 각각에 대해 (키워드당 1콜):
          - 본인 월간검색수 (PC/모바일/합계) + 경쟁정도  [direct-real]
          - 연관키워드 상위 N개 (검색수 기준 정렬)          [direct-real]

        연관키워드를 입력 키워드별로 정확히 매핑하려면 hintKeyword 1개씩
        호출해야 합니다(여러 개 배치 시 연관키워드가 뒤섞임).
        반환: {"keywords": [...], "related": {kw: [...]}}
        """
        if not self.is_configured():
            raise ValueError(
                "네이버 검색광고 API 자격증명(NAVER_AD_*)이 설정되지 않았습니다."
            )

        stats: List[Dict[str, Any]] = []
        related_map: Dict[str, List[Dict[str, Any]]] = {}

        for kw in keywords:
            if not kw.strip():
                continue
            rows = await self._fetch_raw([kw])
            normalized = [self._normalize_row(r) for r in rows]
            kw_norm = kw.replace(" ", "").lower()

            # 1) 입력 키워드 본인 통계 = 결과 중 정규화 일치 행
            own = next(
                (n for n in normalized if n["keyword"].replace(" ", "").lower() == kw_norm),
                None,
            )
            if own:
                stats.append({**own, "input_keyword": kw})
            else:
                # 본인 통계를 못 찾음 → 실측값 없음. 가짜로 채우지 않고 명시.
                logger.warning(f"[KeywordTool] 입력 키워드 '{kw}' 본인 통계 미발견")
                stats.append(
                    {
                        "keyword": kw,
                        "input_keyword": kw,
                        "monthly_pc": None,
                        "monthly_mobile": None,
                        "monthly_total": None,
                        "monthly_masked": False,
                        "monthly_avg_pc_clicks": None,
                        "monthly_avg_mobile_clicks": None,
                        "comp_idx": None,
                        "no_data": True,
                    }
                )

            # 2) 연관키워드 = 본인 제외, 검색수 순 정렬 상위 N
            #    monthly_total 은 마스킹 시 None 일 수 있으므로 None-safe 정렬키.
            related_map[kw] = sorted(
                [n for n in normalized if n["keyword"].replace(" ", "").lower() != kw_norm],
                key=lambda x: x["monthly_total"] if x["monthly_total"] is not None else -1,
                reverse=True,
            )[:related_limit]

        return {"keywords": stats, "related": related_map}
