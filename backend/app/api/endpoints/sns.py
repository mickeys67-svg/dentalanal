"""
SNS 매체 언급량/반응 데이터 (RFP 2-2)

현재 구현:
  - YouTube (공식 Data API v3, 무료 쿼터) : POST /api/v1/sns/youtube  ✅ direct-real

미구현(외부 자격증명/예산·벤더 결정 필요 — 가짜 데이터로 채우지 않음):
  - X (엑스)      : API v2 유료 Bearer Token 필요
  - Instagram     : 공식 API로 임의키워드 해시태그 언급량 불가 → 서드파티 벤더 필요
  - TikTok        : 공식 API 제약 → 서드파티 벤더 필요
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.external_apis.youtube_api import YouTubeClient
from app.api.endpoints.auth import get_current_user
from app.models.models import User

logger = logging.getLogger(__name__)
router = APIRouter()


class YouTubeRequest(BaseModel):
    keyword: str
    max_results: int = Field(25, ge=1, le=50)
    published_after: str | None = None  # RFC3339


@router.post("/youtube")
async def youtube_stats(
    request: YouTubeRequest,
    current_user: User = Depends(get_current_user),
):
    """
    유튜브 검색어 포함 영상 수 + 상위 영상 조회수 집계.
    ⚠️ viewCount는 현재 누적 조회수(시점별 추이 아님), total은 유튜브 공식 근사치.
    """
    client = YouTubeClient()
    if not client.is_configured():
        raise HTTPException(
            status_code=503,
            detail="YouTube API 키(YOUTUBE_API_KEY 또는 GOOGLE_API_KEY)가 서버에 설정되지 않았습니다.",
        )
    if not request.keyword.strip():
        raise HTTPException(status_code=400, detail="키워드가 비어 있습니다.")

    try:
        data = await client.get_keyword_video_stats(
            request.keyword.strip(),
            max_results=request.max_results,
            published_after=request.published_after,
        )
    except Exception as e:
        logger.error(f"[sns/youtube] 조회 실패: {e}")
        raise HTTPException(status_code=502, detail=f"YouTube API 조회 실패: {e}")

    return {"source": "YOUTUBE_DATA_API_V3", **data}


@router.get("/status")
async def sns_status(current_user: User = Depends(get_current_user)):
    """각 SNS 매체 연동 가능 여부(자격증명 존재 기준). 가짜 데이터 없이 실제 상태만 보고."""
    yt = YouTubeClient()
    return {
        "youtube": {
            "supported": True,
            "configured": yt.is_configured(),
            "method": "공식 Data API v3 (무료 쿼터)",
        },
        "x": {
            "supported": True,
            "configured": False,
            "method": "API v2 유료 Bearer Token 필요 (미연동)",
        },
        "instagram": {
            "supported": False,
            "configured": False,
            "method": "공식 API로 임의키워드 언급량 불가 → 서드파티 벤더 구독 필요",
        },
        "tiktok": {
            "supported": False,
            "configured": False,
            "method": "공식 API 제약 → 서드파티 벤더 구독 필요",
        },
    }
