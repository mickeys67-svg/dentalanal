"""
YouTube Data API v3 — 검색어 포함 영상 수 / 조회수 (RFP 2-2 유튜브)
공식 문서: https://developers.google.com/youtube/v3/docs

제공 데이터 (direct-real, 유튜브 공식 API 실측):
  - 검색어 포함 영상 총계(approx, pageInfo.totalResults)
  - 상위 영상 샘플의 조회수/좋아요/댓글수 (statistics)
  - 업로드 월별 영상수 + 해당 영상 누적 조회수 합 (파생)

⚠️ 정직성 주의:
  - statistics.viewCount 는 "현재 누적 조회수"입니다. 시점별 조회수 추이는
    유튜브 공식 API가 제공하지 않습니다(YouTube Analytics API는 본인 채널 한정).
    따라서 "조회수 추이"는 업로드 시점 기준 누적 조회수 분포로만 표현하며,
    이를 실시간 추이로 위장하지 않습니다.
  - search.list 의 totalResults 는 유튜브가 명시적으로 "근사치"라 밝힌 값입니다.

쿼터: search.list = 100 units, videos.list = 1 unit. 일 10,000 units 기본.
자격증명: YOUTUBE_API_KEY (없으면 GOOGLE_API_KEY 폴백)
"""
import logging
from typing import List, Dict, Any, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"


class YouTubeClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.YOUTUBE_API_KEY or settings.GOOGLE_API_KEY

    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def _get(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        params = {**params, "key": self.api_key}
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, params=params)
            if resp.status_code != 200:
                logger.error(f"[YouTube] API error {resp.status_code}: {resp.text[:300]}")
                resp.raise_for_status()
            return resp.json()

    async def get_keyword_video_stats(
        self,
        keyword: str,
        max_results: int = 25,
        published_after: Optional[str] = None,  # RFC3339, e.g. "2024-01-01T00:00:00Z"
    ) -> Dict[str, Any]:
        """
        키워드 검색 → 상위 영상 샘플의 조회수 집계.
        반환:
          {
            "keyword": ...,
            "total_matching_approx": int,   # pageInfo.totalResults (근사)
            "sampled_count": int,
            "total_views_sampled": int,
            "videos": [{videoId,title,channel,publishedAt,viewCount,likeCount,commentCount}],
            "by_upload_month": {"YYYY-MM": {"videos": n, "views": v}},
          }
        """
        if not self.is_configured():
            raise ValueError("YOUTUBE_API_KEY / GOOGLE_API_KEY 미설정 (유튜브 API 사용 불가).")

        search_params: Dict[str, Any] = {
            "part": "snippet",
            "q": keyword,
            "type": "video",
            "maxResults": min(max_results, 50),
            "order": "relevance",
        }
        if published_after:
            search_params["publishedAfter"] = published_after

        search = await self._get(SEARCH_URL, search_params)
        items = search.get("items", [])
        total_approx = int(search.get("pageInfo", {}).get("totalResults", 0))

        video_ids = [
            it["id"]["videoId"]
            for it in items
            if it.get("id", {}).get("videoId")
        ]
        snippet_map = {
            it["id"]["videoId"]: it.get("snippet", {})
            for it in items
            if it.get("id", {}).get("videoId")
        }

        videos: List[Dict[str, Any]] = []
        total_views = 0
        by_month: Dict[str, Dict[str, int]] = {}

        if video_ids:
            stats = await self._get(
                VIDEOS_URL,
                {"part": "statistics,snippet", "id": ",".join(video_ids)},
            )
            for v in stats.get("items", []):
                vid = v.get("id")
                if not vid:
                    continue  # id 없는 항목은 링크/키가 깨지므로 제외
                st = v.get("statistics", {})
                sn = v.get("snippet", snippet_map.get(vid, {}))
                views = int(st.get("viewCount", 0)) if st.get("viewCount") is not None else 0
                published = sn.get("publishedAt", "")
                total_views += views
                videos.append(
                    {
                        "videoId": vid,
                        "title": sn.get("title"),
                        "channel": sn.get("channelTitle"),
                        "publishedAt": published,
                        "viewCount": views,
                        "likeCount": int(st.get("likeCount", 0)) if st.get("likeCount") else 0,
                        "commentCount": int(st.get("commentCount", 0)) if st.get("commentCount") else 0,
                    }
                )
                # 업로드 월별 집계 (파생, 실데이터 합산)
                if len(published) >= 7:
                    mk = published[:7]
                    bucket = by_month.setdefault(mk, {"videos": 0, "views": 0})
                    bucket["videos"] += 1
                    bucket["views"] += views

        videos.sort(key=lambda x: x["viewCount"], reverse=True)

        return {
            "keyword": keyword,
            "total_matching_approx": total_approx,
            "sampled_count": len(videos),
            "total_views_sampled": total_views,
            "videos": videos,
            "by_upload_month": dict(sorted(by_month.items())),
        }
