"""
🕷️ Web Scraper Module
Scrapes content from multiple sources:
- News websites (RSS feeds, HTML)
- Wikipedia articles
- Academic sources
- Social media trends
"""

import asyncio
import aiohttp
import feedparser
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from datetime import datetime
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential
import hashlib

from .source_registry import SourceRegistry


class WebScraper:
    """Asynchronous web scraper with multiple source support."""

    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (compatible; GlobalKnowledgeEngine/1.0; +https://github.com/PranayMahendrakar/global-ai-knowledge-engine)"
    }

    def __init__(self, timeout: int = 30, max_concurrent: int = 10):
        self.timeout = timeout
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.registry = SourceRegistry()
        self._seen_urls: set = set()

    async def scrape_topic(self, topic: str, max_articles: int = 20) -> List[Dict]:
        """Scrape articles for a given topic from multiple sources."""
        logger.info(f"🔍 Scraping topic: '{topic}' (max {max_articles} articles)")
        tasks = []
        sources = self.registry.get_sources_for_topic(topic)

        for source in sources:
            if source["type"] == "rss":
                tasks.append(self._scrape_rss(source["url"], topic))
            elif source["type"] == "web":
                tasks.append(self._scrape_web_search(topic, source["url"]))
            elif source["type"] == "wikipedia":
                tasks.append(self._scrape_wikipedia(topic))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        articles = []
        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"Scraping error: {result}")
                continue
            articles.extend(result)

        # Deduplicate
        unique_articles = self._deduplicate(articles)
        logger.info(f"✅ Got {len(unique_articles)} unique articles for '{topic}'")
        return unique_articles[:max_articles]

    async def _scrape_rss(self, feed_url: str, topic: str) -> List[Dict]:
        """Scrape articles from an RSS feed."""
        articles = []
        try:
            async with aiohttp.ClientSession(headers=self.DEFAULT_HEADERS) as session:
                async with session.get(feed_url, timeout=aiohttp.ClientTimeout(total=self.timeout)) as resp:
                    content = await resp.text()
            feed = feedparser.parse(content)
            for entry in feed.entries[:10]:
                article = {
                    "title": entry.get("title", ""),
                    "url": entry.get("link", ""),
                    "summary": entry.get("summary", ""),
                    "published": entry.get("published", datetime.now().isoformat()),
                    "source": feed_url,
                    "topic": topic,
                    "type": "rss",
                    "text": "",
                    "id": hashlib.md5(entry.get("link", "").encode()).hexdigest()
                }
                if article["url"] and article["title"]:
                    articles.append(article)
                    # Optionally fetch full text
                    if entry.get("link"):
                        full_text = await self._fetch_article_text(entry["link"])
                        article["text"] = full_text
        except Exception as e:
            logger.error(f"RSS scrape error for {feed_url}: {e}")
        return articles

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _fetch_article_text(self, url: str) -> str:
        """Fetch and parse full article text from a URL."""
        if url in self._seen_urls:
            return ""
        self._seen_urls.add(url)

        async with self.semaphore:
            try:
                async with aiohttp.ClientSession(headers=self.DEFAULT_HEADERS) as session:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=self.timeout)) as resp:
                        if resp.status == 200:
                            html = await resp.text()
                            return self._parse_article_text(html)
            except Exception as e:
                logger.warning(f"Failed to fetch {url}: {e}")
        return ""

    def _parse_article_text(self, html: str) -> str:
        """Extract main article text from HTML."""
        soup = BeautifulSoup(html, "lxml")

        # Remove non-content elements
        for tag in soup(["script", "style", "nav", "header", "footer", "aside", "ads"]):
            tag.decompose()

        # Try common article containers
        for selector in ["article", "main", ".article-body", ".post-content", "#content"]:
            container = soup.select_one(selector)
            if container:
                return " ".join(container.get_text(separator=" ").split())[:5000]

        # Fallback: get all paragraph text
        paragraphs = soup.find_all("p")
        text = " ".join(p.get_text() for p in paragraphs if len(p.get_text()) > 50)
        return text[:5000]

    async def _scrape_wikipedia(self, topic: str) -> List[Dict]:
        """Scrape Wikipedia for a topic."""
        articles = []
        try:
            search_url = f"https://en.wikipedia.org/w/api.php"
            params = {
                "action": "query",
                "list": "search",
                "srsearch": topic,
                "format": "json",
                "srlimit": 5
            }
            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, params=params) as resp:
                    data = await resp.json()

            for result in data.get("query", {}).get("search", []):
                page_id = result["pageid"]
                summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{result['title'].replace(' ', '_')}"
                async with aiohttp.ClientSession() as session:
                    async with session.get(summary_url) as resp:
                        if resp.status == 200:
                            page_data = await resp.json()
                            articles.append({
                                "title": page_data.get("title", ""),
                                "url": page_data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                                "text": page_data.get("extract", ""),
                                "summary": page_data.get("extract", "")[:500],
                                "published": datetime.now().isoformat(),
                                "source": "wikipedia",
                                "topic": topic,
                                "type": "wikipedia",
                                "id": hashlib.md5(str(page_id).encode()).hexdigest()
                            })
        except Exception as e:
            logger.error(f"Wikipedia scrape error for '{topic}': {e}")
        return articles

    async def _scrape_web_search(self, topic: str, base_url: str) -> List[Dict]:
        """Scrape search results for a topic."""
        # Placeholder for search engine scraping
        return []

    def _deduplicate(self, articles: List[Dict]) -> List[Dict]:
        """Remove duplicate articles based on URL."""
        seen = set()
        unique = []
        for article in articles:
            key = article.get("url", article.get("id", ""))
            if key and key not in seen:
                seen.add(key)
                unique.append(article)
        return unique

    async def scrape_url(self, url: str, topic: str = "general") -> Optional[Dict]:
        """Scrape a single URL."""
        text = await self._fetch_article_text(url)
        if text:
            soup = BeautifulSoup(requests.get(url, headers=self.DEFAULT_HEADERS, timeout=10).text, "lxml")
            title = soup.find("title")
            return {
                "title": title.get_text() if title else url,
                "url": url,
                "text": text,
                "summary": text[:300],
                "published": datetime.now().isoformat(),
                "source": url,
                "topic": topic,
                "type": "web",
                "id": hashlib.md5(url.encode()).hexdigest()
            }
        return None
