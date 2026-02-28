"""
NaverPlace Scraper - httpx Direct API Call (No Playwright, No Bright Data)

Naver Map의 내부 JSON API를 httpx로 직접 호출.
브라우저 자동화 불필요 - HTTP 요청만으로 순위 데이터 수집.
비용: $0, 속도: <1초
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

HEADERS = {
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
    BASE_URL = "https://map.naver.com/p/api/search/allSearch"

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    async def get_rankings(self, keyword: str) -> list:
        encoded = urllib.parse.quote(keyword)
        url = f"{self.BASE_URL}?query={encoded}&type=all&searchCoord={DEFAULT_COORD}"

        self.logger.info(f"[NaverPlace] '{keyword}' 조회 시작")

        for attempt in range(3):
            try:
                async with httpx.AsyncClient(
                    timeout=15.0,
                    follow_redirects=True,
                ) as client:
                    resp = await client.get(url, headers=HEADERS)

                    self.logger.info(f"[NaverPlace] HTTP {resp.status_code} ('{keyword}')")

                    if resp.status_code == 403:
                        self.logger.warning("[NaverPlace] 403 Forbidden - 잠시 후 재시도")
                        await asyncio.sleep(3 * (attempt + 1))
                        continue

                    if resp.status_code != 200:
                        self.logger.warning(f"[NaverPlace] 비정상 상태코드: {resp.status_code}")
                        await asyncio.sleep(2)
                        continue

                    text = resp.text.strip()

                    # Naver는 가끔 <html><pre>JSON</pre></html> 형태로 반환
                    if text.startswith("<"):
                        match = re.search(r"<pre[^>]*>([\s\S]*?)</pre>", text)
                        if match:
                            text = match.group(1).strip()
                        else:
                            self.logger.error(f"[NaverPlace] HTML 응답에서 JSON 추출 실패")
                            self.logger.debug(f"[NaverPlace] 응답 앞 300자: {text[:300]}")
                            await asyncio.sleep(2)
                            continue

                    data = json.loads(text)
                    results = self._parse_results(data, keyword)
                    self.logger.info(f"[NaverPlace] '{keyword}' → {len(results)}건 수집")
                    return results

            except httpx.TimeoutException:
                self.logger.warning(f"[NaverPlace] 타임아웃 (시도 {attempt + 1}/3)")
                await asyncio.sleep(2)
            except json.JSONDecodeError as e:
                self.logger.error(f"[NaverPlace] JSON 파싱 실패: {e}")
                break
            except Exception as e:
                self.logger.error(f"[NaverPlace] 오류: {type(e).__name__}: {e}")
                import traceback
                self.logger.debug(traceback.format_exc())
                break

        self.logger.error(f"[NaverPlace] '{keyword}' 수집 최종 실패")
        return []

    def _parse_results(self, data: dict, keyword: str) -> list:
        if not isinstance(data, dict):
            self.logger.warning(f"[NaverPlace] 응답이 dict가 아님: {type(data)}")
            return []

        result_obj = data.get("result", {})
        if not result_obj:
            self.logger.warning(f"[NaverPlace] 'result' 키 없음. 최상위 키: {list(data.keys())}")
            return []

        place_obj = result_obj.get("place", {})
        if not place_obj:
            available = list(result_obj.keys()) if isinstance(result_obj, dict) else []
            self.logger.warning(f"[NaverPlace] 'place' 키 없음. result 키: {available}")
            return []

        place_list = place_obj.get("list", [])
        if not place_list:
            self.logger.warning(f"[NaverPlace] 빈 place_list ('{keyword}')")
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
