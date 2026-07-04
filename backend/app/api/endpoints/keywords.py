"""
키워드 인텔리전스 API (RFP 2-1 / 2-3)

- POST /api/v1/keywords/search : 다중 키워드(1~10) 월간검색수 + 연관키워드 조회
  데이터 출처: 네이버 검색광고 키워드도구 API (direct-real, 공식 실측값)
"""
from typing import List, Optional, Dict
from datetime import datetime
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func as sa_func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.external_apis.naver_keyword_tool import NaverKeywordToolClient
from app.external_apis.naver_datalab import NaverDataLabClient
from app.api.endpoints.auth import get_current_user
from app.models.models import User, KeywordSearchStat

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_KEYWORDS = 10


class KeywordSearchRequest(BaseModel):
    keywords: List[str] = Field(..., min_length=1, max_length=MAX_KEYWORDS)
    related_limit: int = Field(20, ge=0, le=100)
    client_id: Optional[str] = None  # 최초검색일 스코프 (없으면 전역)


class KeywordStat(BaseModel):
    keyword: str
    monthly_pc: Optional[int]
    monthly_mobile: Optional[int]
    monthly_total: Optional[int]
    masked: bool = False  # True → "10 미만" 마스킹 포함(실측 아님). 값은 None일 수 있음.
    comp_idx: Optional[str]
    no_data: bool = False
    first_seen: Optional[str] = None  # 최초검색일 (RFP 2-1), ISO date. 없으면 이번이 최초.


class RelatedKeyword(BaseModel):
    keyword: str
    monthly_total: Optional[int]  # 마스킹("< 10") 시 None
    masked: bool = False


class KeywordSearchResponse(BaseModel):
    source: str = "NAVER_SEARCHAD_KEYWORDTOOL"  # 데이터 출처 명시 (실측)
    keywords: List[KeywordStat]
    related: dict  # {input_keyword: [RelatedKeyword, ...]}


def _persist_and_first_seen(
    db: Session, term: str, client_id: Optional[str], stat: dict
) -> Optional[str]:
    """
    키워드 스냅샷 저장 + 최초검색일 반환.
    - 최초검색일 = 신규 저장 이전 기존 MIN(captured_at). 없으면(이번이 최초) None.
    - DB 오류가 조회 결과를 깨뜨리지 않도록 호출측에서 개별 커밋/롤백 처리.
    반환: 최초검색일 ISO date 문자열 또는 None.
    """
    q = db.query(sa_func.min(KeywordSearchStat.captured_at)).filter(
        KeywordSearchStat.term == term
    )
    if client_id:
        q = q.filter(KeywordSearchStat.client_id == client_id)
    prior_min = q.scalar()
    first_seen = prior_min.date().isoformat() if prior_min else None

    db.add(
        KeywordSearchStat(
            id=uuid.uuid4(),
            client_id=client_id,
            term=term,
            monthly_pc=stat.get("monthly_pc"),
            monthly_mobile=stat.get("monthly_mobile"),
            monthly_total=stat.get("monthly_total"),
            comp_idx=stat.get("comp_idx"),
        )
    )
    return first_seen


@router.post("/search", response_model=KeywordSearchResponse)
async def search_keywords(
    request: KeywordSearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    다중 키워드 월간검색수 + 연관키워드 조회.
    모든 수치는 네이버 검색광고 키워드도구 공식 API 실측값(direct-real).
    각 키워드 검색 이력을 저장해 최초검색일(RFP 2-1)을 산출.
    """
    # 빈 문자열 제거 + 중복 제거(순서 유지)
    seen = set()
    cleaned: List[str] = []
    for k in request.keywords:
        k = k.strip()
        if k and k not in seen:
            seen.add(k)
            cleaned.append(k)

    if not cleaned:
        raise HTTPException(status_code=400, detail="유효한 키워드가 없습니다.")

    client = NaverKeywordToolClient()
    if not client.is_configured():
        raise HTTPException(
            status_code=503,
            detail="네이버 검색광고 API 자격증명(NAVER_AD_*)이 서버에 설정되지 않았습니다.",
        )

    try:
        result = await client.get_keyword_stats(cleaned, related_limit=request.related_limit)
    except Exception as e:
        logger.error(f"[keywords/search] 조회 실패: {e}")
        raise HTTPException(status_code=502, detail=f"네이버 API 조회 실패: {e}")

    # 최초검색일 산출 + 스냅샷 저장. DB 실패는 조회 결과를 막지 않음(부가 기능).
    first_seen_map: Dict[str, Optional[str]] = {}
    try:
        for s in result["keywords"]:
            term = s["input_keyword"]
            first_seen_map[term] = _persist_and_first_seen(
                db, term, request.client_id, s
            )
        db.commit()
    except Exception as e:
        db.rollback()
        logger.warning(f"[keywords/search] 최초검색일 저장 실패(조회 결과는 정상 반환): {e}")
        first_seen_map = {}

    keywords = [
        KeywordStat(
            keyword=s["input_keyword"],
            monthly_pc=s["monthly_pc"],
            monthly_mobile=s["monthly_mobile"],
            monthly_total=s["monthly_total"],
            masked=s.get("monthly_masked", False),
            comp_idx=s["comp_idx"],
            no_data=s.get("no_data", False),
            first_seen=first_seen_map.get(s["input_keyword"]),
        )
        for s in result["keywords"]
    ]
    related = {
        kw: [
            RelatedKeyword(
                keyword=r["keyword"],
                monthly_total=r["monthly_total"],
                masked=r.get("monthly_masked", False),
            ).model_dump()
            for r in items
        ]
        for kw, items in result["related"].items()
    }

    return KeywordSearchResponse(keywords=keywords, related=related)


class RecentKeywordsResponse(BaseModel):
    terms: List[str]


@router.get("/recent", response_model=RecentKeywordsResponse)
async def recent_keywords(
    limit: int = 8,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    최근 검색한 키워드 목록(중복 제거, 최신순)을 반환.
    저장된 KeywordSearchStat(네이버 실측 스냅샷)에서 term별 최신 captured_at 기준 정렬.
    → 프론트가 로그인 후 진입 시 이 목록으로 실데이터 조회를 자동 복원(빈 화면 방지).
    """
    limit = max(1, min(limit, MAX_KEYWORDS))
    last_seen = sa_func.max(KeywordSearchStat.captured_at).label("last_seen")
    rows = (
        db.query(KeywordSearchStat.term, last_seen)
        .group_by(KeywordSearchStat.term)
        .order_by(last_seen.desc())
        .limit(limit)
        .all()
    )
    return RecentKeywordsResponse(terms=[r[0] for r in rows])


# =========================================================================
# 데이터랩 검색어 트렌드 (RFP 2-3) — 상대지수(0~100). 절대검색량 아님.
# =========================================================================

DOW_LABELS = ["월", "화", "수", "목", "금", "토", "일"]


class TrendRequest(BaseModel):
    keywords: List[str] = Field(..., min_length=1, max_length=5)  # 데이터랩 최대 5그룹
    start_date: str  # YYYY-MM-DD
    end_date: str
    time_unit: str = Field("date", pattern="^(date|week|month)$")
    device: str = Field("", pattern="^(|pc|mo)$")
    gender: str = Field("", pattern="^(|m|f)$")
    ages: Optional[List[str]] = None


def _aggregate_month_dow(series: List[Dict]) -> Dict[str, Dict[str, float]]:
    """
    일별 상대지수 시계열 → 월별/요일별 상대 분포(파생).
    [derived-formula] 실데이터(일별 ratio) 합산. 임의값 없음.
    period 가 YYYY-MM-DD(일별)일 때만 요일 집계 가능.
    """
    by_month: Dict[str, float] = {}
    by_dow: Dict[str, float] = {}
    for p in series:
        period = p.get("period")
        ratio = p.get("ratio")
        if not period or not isinstance(ratio, (int, float)):
            continue
        # 월별
        month_key = period[:7]  # YYYY-MM
        by_month[month_key] = round(by_month.get(month_key, 0) + ratio, 2)
        # 요일별 (일별 데이터에서만)
        try:
            dt = datetime.strptime(period, "%Y-%m-%d")
            dow = DOW_LABELS[dt.weekday()]
            by_dow[dow] = round(by_dow.get(dow, 0) + ratio, 2)
        except ValueError:
            pass
    return {"by_month": by_month, "by_dow": by_dow}


@router.post("/trend")
async def keyword_trend(
    request: TrendRequest,
    current_user: User = Depends(get_current_user),
):
    """
    검색어 트렌드 (일/주/월 단위) + 월별·요일별 파생 분포.
    ⚠️ 값은 네이버 데이터랩 상대지수(기간 내 최대=100). 절대 검색수 아님.
    """
    client = NaverDataLabClient()
    if not client.is_configured():
        raise HTTPException(
            status_code=503,
            detail="네이버 오픈API 자격증명(NAVER_CLIENT_ID/SECRET)이 서버에 설정되지 않았습니다.",
        )
    keywords = [k.strip() for k in request.keywords if k.strip()]
    if not keywords:
        raise HTTPException(status_code=400, detail="유효한 키워드가 없습니다.")

    try:
        series = await client.get_trend_series(
            keywords,
            request.start_date,
            request.end_date,
            request.time_unit,
            request.device,
            request.gender,
            request.ages,
        )
    except Exception as e:
        logger.error(f"[keywords/trend] 조회 실패: {e}")
        raise HTTPException(status_code=502, detail=f"네이버 데이터랩 조회 실패: {e}")

    # 각 키워드에 월별/요일별 파생 분포 첨부
    enriched = []
    for s in series:
        agg = _aggregate_month_dow(s["series"])
        enriched.append({**s, **agg})

    return {
        "source": "NAVER_DATALAB_SEARCH_TREND",
        "value_type": "RELATIVE_INDEX_0_100",  # 절대검색량 아님 명시
        "note": "값은 상대지수(기간 내 최대=100). 절대 검색수가 아닙니다.",
        "results": enriched,
    }


class DemographicsRequest(BaseModel):
    keyword: str
    start_date: str
    end_date: str


@router.post("/demographics")
async def keyword_demographics(
    request: DemographicsRequest,
    current_user: User = Depends(get_current_user),
):
    """
    단일 키워드 성별/연령대 상대 관심도 지수.
    ⚠️ 인구 비율이 아니라 상대 관심도(데이터랩 정규화 특성). client 에서 그대로 라벨링할 것.
    """
    client = NaverDataLabClient()
    if not client.is_configured():
        raise HTTPException(
            status_code=503,
            detail="네이버 오픈API 자격증명(NAVER_CLIENT_ID/SECRET)이 서버에 설정되지 않았습니다.",
        )
    if not request.keyword.strip():
        raise HTTPException(status_code=400, detail="키워드가 비어 있습니다.")

    try:
        data = await client.get_demographics(
            request.keyword.strip(), request.start_date, request.end_date
        )
    except Exception as e:
        logger.error(f"[keywords/demographics] 조회 실패: {e}")
        raise HTTPException(status_code=502, detail=f"네이버 데이터랩 조회 실패: {e}")

    return {"source": "NAVER_DATALAB_SEARCH_TREND", **data}
