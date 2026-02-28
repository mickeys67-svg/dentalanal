"""
NaverView Scraper - httpx + BeautifulSoup HTML 스크래핑 (API 키 불필요)

전략:
1. [우선] NAVER_CLIENT_ID/SECRET 있으면 공식 Search API 사용 (정확도 높음)
2. [폴백] 없으면 Naver 검색 결과 페이지 HTML 직접 파싱

비용: $0, API 키 없어도 동작
"""
import httpx
import logging
import asyncio
import re
from bs4 import BeautifulSoup
from html import unescape

logger = logging.getLogger(__name__)


def _clean_html_tags(text: str) -> str:
    """HTML 태그 및 엔티티 제거"""
    text = re.sub(r"<[^>]+>", "", text)
    return unescape(text).strip()


class NaverViewScraper:
    SEARCH_URL = "https://search.naver.com/search.naver"

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

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        # 공식 API 키가 있으면 우선 사용
        self._api_client = self._try_load_api_client()

    def _try_load_api_client(self):
        try:
            from app.external_apis.naver_search import NaverSearchClient
            from app.core.config import settings
            if settings.NAVER_CLIENT_ID and settings.NAVER_CLIENT_SECRET:
                self.logger.info("[NaverView] 공식 Search API 키 감지 - API 모드 사용")
                return NaverSearchClient()
        except Exception:
            pass
        self.logger.info("[NaverView] API 키 없음 - HTML 스크래핑 모드 사용")
        return None

    async def get_rankings(self, keyword: str) -> list:
        # 공식 API 우선 시도
        if self._api_client:
            try:
                results = await self._fetch_via_api(keyword)
                if results:
                    return results
                self.logger.warning("[NaverView] API 결과 없음, HTML 폴백 시도")
            except Exception as e:
                self.logger.warning(f"[NaverView] API 오류: {e}, HTML 폴백 시도")

        # HTML 스크래핑 폴백
        return await self._fetch_via_html(keyword)

    # ─────────────────────────────────────────
    # 방법 A: 공식 Naver Search API
    # ─────────────────────────────────────────
    async def _fetch_via_api(self, keyword: str) -> list:
        blog_data = await self._api_client.search_blog(keyword, display=50, sort="sim")
        cafe_data = await self._api_client.search_cafe(keyword, display=20, sort="sim")

        items = []
        for item in blog_data.get("items", []):
            items.append({
                "title": _clean_html_tags(item.get("title", "")),
                "blog_name": item.get("bloggername", ""),
                "link": item.get("link", ""),
                "keyword": keyword,
                "created_at": self._format_date(item.get("postdate", "")),
                "is_ad": False,
                "snippet": _clean_html_tags(item.get("description", "")),
                "source_type": "Blog",
            })
        for item in cafe_data.get("items", []):
            items.append({
                "title": _clean_html_tags(item.get("title", "")),
                "blog_name": item.get("cafename", ""),
                "link": item.get("link", ""),
                "keyword": keyword,
                "created_at": self._format_date(item.get("postdate", "")),
                "is_ad": False,
                "snippet": _clean_html_tags(item.get("description", "")),
                "source_type": "Cafe",
            })

        for i, item in enumerate(items):
            item["rank"] = i + 1

        self.logger.info(f"[NaverView API] '{keyword}' → {len(items)}건")
        return items

    # ─────────────────────────────────────────
    # 방법 B: HTML 직접 스크래핑
    # ─────────────────────────────────────────
    async def _fetch_via_html(self, keyword: str) -> list:
        params = {
            "where": "view",
            "sm": "tab_jum",
            "query": keyword,
        }

        self.logger.info(f"[NaverView HTML] '{keyword}' 스크래핑 시작")

        for attempt in range(3):
            try:
                async with httpx.AsyncClient(
                    timeout=20.0,
                    follow_redirects=True,
                ) as client:
                    resp = await client.get(
                        self.SEARCH_URL,
                        params=params,
                        headers=self.HEADERS,
                    )

                    self.logger.info(f"[NaverView HTML] HTTP {resp.status_code} ('{keyword}')")

                    if resp.status_code != 200:
                        await asyncio.sleep(2)
                        continue

                    results = self._parse_view_html(resp.text, keyword)
                    self.logger.info(f"[NaverView HTML] '{keyword}' → {len(results)}건")
                    return results

            except httpx.TimeoutException:
                self.logger.warning(f"[NaverView HTML] 타임아웃 (시도 {attempt + 1}/3)")
                await asyncio.sleep(2)
            except Exception as e:
                self.logger.error(f"[NaverView HTML] 오류: {type(e).__name__}: {e}")
                break

        return []

    def _parse_view_html(self, html: str, keyword: str) -> list:
        soup = BeautifulSoup(html, "html.parser")
        results = []

        # Naver VIEW 탭 결과 컨테이너 (여러 셀렉터 시도 - UI 변경 대응)
        # Strategy 1: .lst_total .bx (최신 구조)
        items = soup.select(".lst_total .bx")

        # Strategy 2: .total_area .bx
        if not items:
            items = soup.select(".total_area .bx")

        # Strategy 3: .view_tab1 .lst_total li (구형 구조)
        if not items:
            items = soup.select(".view_tab1 .lst_total li")

        # Strategy 4: 더 넓은 셀렉터
        if not items:
            items = soup.select(".api_subject_bx")

        self.logger.debug(f"[NaverView HTML] 파싱된 아이템 수: {len(items)}")

        for idx, item in enumerate(items):
            try:
                # 제목 추출
                title_tag = (
                    item.select_one(".total_tit a")
                    or item.select_one(".api_txt_lines.total_tit")
                    or item.select_one("a.link_tit")
                    or item.select_one(".title_area a")
                    or item.select_one("a[class*='tit']")
                )
                if not title_tag:
                    continue

                title = _clean_html_tags(title_tag.get_text())
                link = title_tag.get("href", "")

                # 블로그명/작성자
                author_tag = (
                    item.select_one(".sub_name")
                    or item.select_one(".name")
                    or item.select_one(".user_name")
                    or item.select_one(".source a")
                )
                author = author_tag.get_text(strip=True) if author_tag else "Unknown"

                # 날짜
                date_tag = (
                    item.select_one(".sub_time")
                    or item.select_one("time")
                    or item.select_one(".date")
                    or item.select_one("[class*='date']")
                )
                date = ""
                if date_tag:
                    date = date_tag.get("datetime", "") or date_tag.get_text(strip=True)

                # 본문 요약
                desc_tag = (
                    item.select_one(".total_dsc")
                    or item.select_one(".api_txt_lines.dsc_txt")
                    or item.select_one(".dsc_txt")
                    or item.select_one(".desc")
                )
                snippet = _clean_html_tags(desc_tag.get_text()) if desc_tag else ""

                if not title:
                    continue

                results.append({
                    "rank": idx + 1,
                    "title": title,
                    "blog_name": author,
                    "link": link,
                    "keyword": keyword,
                    "created_at": date,
                    "is_ad": False,
                    "snippet": snippet[:200],
                    "source_type": "Blog",
                })

            except Exception as e:
                self.logger.debug(f"[NaverView HTML] 아이템 파싱 오류: {e}")
                continue

        # 결과가 없으면 HTML 저장해서 디버깅 (로컬 환경에서만 유용)
        if not results:
            self.logger.warning(
                f"[NaverView HTML] '{keyword}' 결과 없음. "
                f"HTML 길이: {len(html)}자. 셀렉터가 변경되었을 수 있음."
            )

        return results

    @staticmethod
    def _format_date(date_str: str) -> str:
        if len(date_str) == 8:
            return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
        return date_str
