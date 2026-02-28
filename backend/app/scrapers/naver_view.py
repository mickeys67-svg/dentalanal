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
        """
        Naver VIEW 탭 HTML 파싱.

        Naver가 React 앱으로 전환하여 클래스명이 해시화됨.
        안정적 접근: blog.naver.com/{user}/{postId} URL 패턴으로 직접 추출.
        """
        import re as _re
        soup = BeautifulSoup(html, "html.parser")
        results = []
        seen_urls: set = set()

        # 블로그 포스트 URL 패턴: blog.naver.com/{username}/{12자리 이상 숫자 ID}
        POST_URL_RE = _re.compile(r"https://blog\.naver\.com/[A-Za-z0-9_]+/\d{8,}")

        all_post_links = soup.find_all("a", href=POST_URL_RE)
        self.logger.debug(f"[NaverView HTML] blog.naver.com 포스트 링크: {len(all_post_links)}개")

        for link in all_post_links:
            href = link.get("href", "")
            if href in seen_urls:
                continue

            title = _clean_html_tags(link.get_text()).strip()
            if len(title) < 5:
                continue

            seen_urls.add(href)

            # 블로그 사용자명을 URL에서 추출 (display name 대신 안정적인 ID)
            m = _re.match(r"https://blog\.naver\.com/([A-Za-z0-9_]+)/", href)
            blog_id = m.group(1) if m else "Unknown"

            # 같은 컨테이너 내 display name 탐색 (sds-comps-profile-info-title-text)
            blog_name = blog_id
            parent = link.find_parent()
            depth = 0
            while parent and depth < 6:
                profile_link = parent.find(
                    "a",
                    href=_re.compile(rf"blog\.naver\.com/{_re.escape(blog_id)}$"),
                )
                if profile_link:
                    display = profile_link.get_text().strip()
                    if display:
                        blog_name = display
                    break
                parent = parent.find_parent()
                depth += 1

            results.append({
                "rank": len(results) + 1,
                "title": title,
                "blog_name": blog_name,
                "link": href,
                "keyword": keyword,
                "created_at": "",
                "is_ad": False,
                "snippet": "",
                "source_type": "Blog",
            })

            if len(results) >= 30:
                break

        if not results:
            self.logger.warning(
                f"[NaverView HTML] '{keyword}' 결과 없음. "
                f"HTML 길이: {len(html)}자."
            )

        return results

    @staticmethod
    def _format_date(date_str: str) -> str:
        if len(date_str) == 8:
            return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
        return date_str
