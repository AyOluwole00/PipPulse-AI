"""
NewsAPI Collector Module
Collects Forex-related news from NewsAPI
"""

from typing import List, Optional
from datetime import datetime, timedelta
import aiohttp
import asyncio
import hashlib

from app.collectors.base import BaseCollector
from app.schemas import RawNewsItem, SourceType
from app.config import get_settings


class NewsAPICollector(BaseCollector):
    """Collector for NewsAPI"""

    def __init__(self):
        super().__init__(SourceType.NEWSAPI)
        self.settings = get_settings()
        self.api_key = self.settings.newsapi_key
        self.base_url = "https://newsapi.org/v2"
        self.session: Optional[aiohttp.ClientSession] = None

    async def authenticate(self) -> bool:
        """Authenticate with NewsAPI"""
        if not self.api_key:
            print("NewsAPI key not configured")
            return False

        # NewsAPI uses API key in headers, no separate auth needed
        return True

    async def collect(self) -> List[RawNewsItem]:
        """Collect news from NewsAPI"""
        if not await self.authenticate():
            return []

        items = []

        try:
            if not self.session:
                self.session = aiohttp.ClientSession()

            # Get news for each category
            for category in self.settings.news_categories:
                category_items = await self.fetch_news_by_category(category)
                items.extend(category_items)

                # Rate limiting
                await asyncio.sleep(1)

        except Exception as e:
            print(f"Error collecting from NewsAPI: {e}")

        return items

    async def fetch_news_by_category(self, category: str) -> List[RawNewsItem]:
        """Fetch news by category"""
        items = []

        try:
            # Get news from the last hour
            from_date = (datetime.utcnow() - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S")

            params = {
                "category": category,
                "language": ",".join(self.settings.news_languages),
                "apiKey": self.api_key,
                "from": from_date,
                "sortBy": "publishedAt",
                "pageSize": 100
            }

            async with self.session.get(
                f"{self.base_url}/top-headlines",
                params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()

                    if data.get("status") == "ok":
                        for article in data.get("articles", []):
                            item = self.parse_article(article)
                            if item:
                                items.append(item)
                else:
                    error_text = await response.text()
                    print(f"NewsAPI error: {response.status} - {error_text}")

        except Exception as e:
            print(f"Error fetching news by category: {e}")

        return items

    def parse_article(self, article: dict) -> Optional[RawNewsItem]:
        """Parse article from NewsAPI response"""
        try:
            title = article.get("title", "")
            description = article.get("description", "")
            content = article.get("content", "")

            # Combine title and description for better analysis
            full_content = f"{title}. {description} {content}".strip()

            # Filter for Forex-related content
            if not self.is_forex_related(full_content):
                return None

            # Parse timestamp
            published_at = article.get("publishedAt")
            if published_at:
                timestamp = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
            else:
                timestamp = datetime.utcnow()

            # Extract currency pairs
            currency_pairs = self.extract_currency_pairs(full_content)

            # Create source ID
            url = article.get("url", "")
            source_id = hashlib.md5(url.encode()).hexdigest() if url else str(hash(full_content))

            return RawNewsItem(
                source=SourceType.NEWSAPI,
                source_id=source_id,
                content=full_content,
                title=title,
                author=article.get("author"),
                url=url if url else None,
                timestamp=timestamp,
                currency_pairs=currency_pairs,
                metadata={
                    "source_name": article.get("source", {}).get("name", "Unknown"),
                    "category": article.get("category", "general")
                }
            )

        except Exception as e:
            print(f"Error parsing article: {e}")
            return None

    def is_forex_related(self, text: str) -> bool:
        """Check if content is Forex-related"""
        forex_keywords = [
            "forex", "currency", "exchange rate", "dollar", "euro", "pound",
            "yen", "franc", "central bank", "federal reserve", "ecb", "boj",
            "inflation", "interest rate", "monetary policy", "gdp", "trade",
            "eur/usd", "gbp/usd", "usd/jpy", "usd/chf", "aud/usd", "usd/cad"
        ]

        text_lower = text.lower()
        return any(keyword in text_lower for keyword in forex_keywords)

    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()
