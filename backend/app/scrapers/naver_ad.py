"""
NaverAd Scraper - httpx 직접 호출 + BeautifulSoup

네이버 검색 결과 파워링크(광고) 파싱.
Playwright 제거, httpx 직접 사용.
"""
import httpx
import urllib.parse
import logging
import asyncio
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    ),
    "Referer": "https://search.naver.com/",
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


class NaverAdScraper:
    SEARCH_URL = "https://search.naver.com/search.naver"

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    async def get_ad_rankings(self, keyword: str) -> list:
        params = {
            "where": "nexearch",
            "sm": "top_hty",
            "fbm": "0",
            "ie": "utf8",
            "query": keyword,
        }

        self.logger.info(f"[NaverAd] '{keyword}' 광고 순위 조회")

        for attempt in range(3):
            try:
                async with httpx.AsyncClient(
                    timeout=15.0,
                    follow_redirects=True,
                ) as client:
                    resp = await client.get(
                        self.SEARCH_URL, params=params, headers=HEADERS
                    )

                    self.logger.info(f"[NaverAd] HTTP {resp.status_code} ('{keyword}')")

                    if resp.status_code != 200:
                        await asyncio.sleep(2)
                        continue

                    results = self._parse_ad_html(resp.text, keyword)
                    self.logger.info(f"[NaverAd] '{keyword}' → {len(results)}건")
                    return results

            except httpx.TimeoutException:
                self.logger.warning(f"[NaverAd] 타임아웃 (시도 {attempt + 1}/3)")
                await asyncio.sleep(2)
            except Exception as e:
                self.logger.error(f"[NaverAd] 오류: {type(e).__name__}: {e}")
                break

        return []

    def _parse_ad_html(self, html: str, keyword: str) -> list:
        soup = BeautifulSoup(html, "html.parser")
        results = []

        # 파워링크 광고 컨테이너 탐색 (여러 셀렉터 - UI 변경 대응)
        ad_list = (
            soup.select(".power_link_body .lst_type > li")
            or soup.select("ul.lst_type > li[data-atrank]")
            or soup.select(".ad_section ul > li")
            or soup.select("li.lst_type")
        )

        if not ad_list:
            # 파워링크 섹션 자체를 넓게 찾기
            power_section = (
                soup.find(id="power_link_body")
                or soup.find(class_="power_link_body")
                or soup.find(class_="ad_pack")
            )
            if power_section:
                ad_list = power_section.select("li")

        self.logger.debug(f"[NaverAd] 광고 항목 수: {len(ad_list)}")

        for index, item in enumerate(ad_list):
            try:
                # 제목
                title_tag = (
                    item.select_one(".lnk_tit")
                    or item.select_one("a.tit")
                    or item.select_one(".ad_tit a")
                    or item.select_one("a[class*='tit']")
                )
                if not title_tag:
                    continue
                title = title_tag.get_text(strip=True)
                if not title:
                    continue

                # 표시 URL
                url_tag = (
                    item.select_one(".url_area .url")
                    or item.select_one(".ad_url")
                    or item.select_one(".dsp_url")
                )
                display_url = url_tag.get_text(strip=True) if url_tag else ""

                # 설명
                desc_tag = (
                    item.select_one(".ad_dsc .dsc")
                    or item.select_one(".dsc_txt")
                    or item.select_one(".ad_desc")
                )
                description = desc_tag.get_text(strip=True) if desc_tag else ""

                results.append({
                    "rank": len(results) + 1,
                    "advertiser": title,
                    "title": title,
                    "description": description,
                    "display_url": display_url,
                    "keyword": keyword,
                })

            except Exception as e:
                self.logger.debug(f"[NaverAd] 항목 파싱 오류: {e}")
                continue

        if not results:
            self.logger.warning(
                f"[NaverAd] '{keyword}' 광고 없음. "
                "네이버 UI가 변경되었거나 해당 키워드에 광고가 없을 수 있음."
            )

        return results
