"""
NaverPlace Scraper

우선순위:
1. [우선] NAVER_CLIENT_ID/SECRET 있으면 공식 Local Search API 사용 (안정적)
2. [폴백] Naver Map 내부 API 직접 호출 (한국 IP에서만 CAPTCHA 없이 작동)

비용: $0
"""
import httpx
import urllib.parse
import json
import logging
import asyncio
import re

logger = logging.getLogger(__name__)

# 강남 좌표 기본값 (치과 밀집 지역)
DEFAULT_COORD = "127.027610%3B37.498095"

MAP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
    ),
    "Referer": "https://map.naver.com/",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Origin": "https://map.naver.com",
}


class NaverPlaceScraper:
    MAP_API_URL = "https://map.naver.com/p/api/search/allSearch"
    LOCAL_API_URL = "https://openapi.naver.com/v1/search/local"

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._client_id, self._client_secret = self._load_api_credentials()

    def _load_api_credentials(self):
        try:
            from app.core.config import settings
            cid = getattr(settings, "NAVER_CLIENT_ID", None)
            secret = getattr(settings, "NAVER_CLIENT_SECRET", None)
            if cid and secret:
                self.logger.info("[NaverPlace] Naver Search API 키 감지 - Local API 모드 사용")
                return cid, secret
        except Exception:
            pass
        self.logger.info("[NaverPlace] API 키 없음 - Map API 직접 호출 모드 (한국 IP 필요)")
        return None, None

    async def get_rankings(self, keyword: str) -> list:
        # 공식 Local Search API 우선
        if self._client_id and self._client_secret:
            try:
                results = await self._fetch_via_local_api(keyword)
                if results:
                    return results
                self.logger.warning("[NaverPlace] Local API 결과 없음, Map API 폴백 시도")
            except Exception as e:
                self.logger.warning(f"[NaverPlace] Local API 오류: {e}, Map API 폴백 시도")

        # Map API 폴백 (한국 IP 환경에서 작동)
        return await self._fetch_via_map_api(keyword)

    # ─────────────────────────────────────────
    # 방법 A: Naver Local Search API (공식)
    # ─────────────────────────────────────────

    async def _fetch_via_local_api(self, keyword: str) -> list:
        """Naver 공식 Local Search API - CLIENT_ID/SECRET 필요, 무료 25,000회/일."""
        headers = {
            "X-Naver-Client-Id": self._client_id,
            "X-Naver-Client-Secret": self._client_secret,
        }

        all_items = []
        display = 5   # local API 최대 5개/페이지
        max_results = 25

        for start in range(1, max_results + 1, display):
            params = {
                "query": keyword,
                "display": display,
                "start": start,
                "sort": "random",   # 관련도 순
            }
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(
                        self.LOCAL_API_URL, headers=headers, params=params
                    )
                    if resp.status_code == 401:
                        self.logger.error("[NaverPlace] Local API 인증 실패 (CLIENT_ID/SECRET 확인)")
                        break
                    if resp.status_code != 200:
                        self.logger.warning(f"[NaverPlace] Local API HTTP {resp.status_code}")
                        break
                    data = resp.json()
                    items = data.get("items", [])
                    if not items:
                        break
                    all_items.extend(items)
                    if len(items) < display:
                        break
            except Exception as e:
                self.logger.error(f"[NaverPlace] Local API 요청 오류: {e}")
                break

        results = []
        for i, item in enumerate(all_items):
            # API는 <b>태그로 키워드 강조하므로 제거
            name = re.sub(r"<[^>]+>", "", item.get("title", "")).strip()
            if not name:
                continue
            results.append({
                "rank": i + 1,
                "name": name,
                "id": "",
                "category": item.get("category", ""),
                "road_address": item.get("roadAddress", ""),
                "keyword": keyword,
                "lat": item.get("mapy", ""),
                "lng": item.get("mapx", ""),
            })

        self.logger.info(f"[NaverPlace Local API] '{keyword}' → {len(results)}건")
        return results

    # ─────────────────────────────────────────
    # 방법 B: Naver Map 내부 API (폴백)
    # ─────────────────────────────────────────

    async def _fetch_via_map_api(self, keyword: str) -> list:
        """Naver Map 내부 JSON API - 한국 IP에서 CAPTCHA 없이 작동."""
        encoded = urllib.parse.quote(keyword)
        url = f"{self.MAP_API_URL}?query={encoded}&type=all&searchCoord={DEFAULT_COORD}"

        self.logger.info(f"[NaverPlace Map] '{keyword}' Map API 조회")

        for attempt in range(2):
            try:
                async with httpx.AsyncClient(
                    timeout=15.0,
                    follow_redirects=True,
                ) as client:
                    resp = await client.get(url, headers=MAP_HEADERS)

                    self.logger.info(f"[NaverPlace Map] HTTP {resp.status_code}")

                    if resp.status_code == 403:
                        self.logger.warning("[NaverPlace Map] 403 - 접근 차단")
                        await asyncio.sleep(3)
                        continue

                    if resp.status_code != 200:
                        await asyncio.sleep(2)
                        continue

                    text = resp.text.strip()
                    if text.startswith("<"):
                        match = re.search(r"<pre[^>]*>([\s\S]*?)</pre>", text)
                        if match:
                            text = match.group(1).strip()
                        else:
                            self.logger.warning("[NaverPlace Map] HTML 응답 - JSON 추출 불가")
                            break

                    data = json.loads(text)

                    # CAPTCHA 차단 확인
                    result_obj = data.get("result", {})
                    if result_obj and result_obj.get("ncaptcha"):
                        self.logger.warning(
                            "[NaverPlace Map] CAPTCHA 차단 감지 (해외 IP). "
                            "NAVER_CLIENT_ID/SECRET 설정 시 Local Search API로 대체됩니다."
                        )
                        return []

                    results = self._parse_map_results(data, keyword)
                    self.logger.info(f"[NaverPlace Map] '{keyword}' → {len(results)}건")
                    return results

            except httpx.TimeoutException:
                self.logger.warning(f"[NaverPlace Map] 타임아웃 (시도 {attempt + 1}/2)")
                await asyncio.sleep(2)
            except json.JSONDecodeError as e:
                self.logger.error(f"[NaverPlace Map] JSON 파싱 실패: {e}")
                break
            except Exception as e:
                self.logger.error(f"[NaverPlace Map] 오류: {type(e).__name__}: {e}")
                break

        self.logger.error(
            f"[NaverPlace] '{keyword}' 수집 실패. "
            "해결: Naver Developers (developers.naver.com)에서 "
            "NAVER_CLIENT_ID / NAVER_CLIENT_SECRET 발급 필요."
        )
        return []

    def _parse_map_results(self, data: dict, keyword: str) -> list:
        if not isinstance(data, dict):
            return []

        result_obj = data.get("result", {})
        if not result_obj:
            return []

        place_obj = result_obj.get("place")
        if not place_obj:
            return []

        place_list = place_obj.get("list", [])
        if not place_list:
            return []

        results = []
        for index, item in enumerate(place_list):
            name = item.get("name", "").strip()
            if not name:
                continue
            results.append({
                "rank": index + 1,
                "name": name,
                "id": item.get("id", ""),
                "category": item.get("category", ""),
                "road_address": item.get("roadAddress", ""),
                "keyword": keyword,
                "lat": item.get("y", ""),
                "lng": item.get("x", ""),
            })

        return results
