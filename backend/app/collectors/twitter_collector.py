"""
Twitter/X Collector Module
Collects Forex-related tweets using Twitter API v2
"""

from typing import List, Optional
from datetime import datetime, timedelta
import tweepy
import asyncio

from app.collectors.base import BaseCollector
from app.schemas import RawNewsItem, SourceType
from app.config import get_settings


class TwitterCollector(BaseCollector):
    """Collector for Twitter/X API"""

    def __init__(self):
        super().__init__(SourceType.TWITTER)
        self.settings = get_settings()
        self.bearer_token = self.settings.twitter_bearer_token
        self.api_key = self.settings.twitter_api_key
        self.api_secret = self.settings.twitter_api_secret
        self.access_token = self.settings.twitter_access_token
        self.access_secret = self.settings.twitter_access_secret
        self.client: Optional[tweepy.Client] = None

        # Forex-related hashtags and keywords
        self.forex_keywords = [
            "#forex", "#currency", "#eurusd", "#gbpusd", "#usdjpy",
            "#usdchf", "#audusd", "#usdcad", "#nzdusd",
            "forex", "currency", "exchange rate", "dollar", "euro", "pound",
            "yen", "franc", "central bank", "federal reserve", "ecb", "boj"
        ]

    async def authenticate(self) -> bool:
        """Authenticate with Twitter API"""
        if not self.bearer_token:
            print("Twitter bearer token not configured")
            return False

        try:
            # Create Twitter client
            self.client = tweepy.Client(
                bearer_token=self.bearer_token,
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_secret,
                wait_on_rate_limit=True
            )

            # Test connection
            self.client.get_me()

            return True

        except Exception as e:
            print(f"Twitter authentication error: {e}")
            return False

    async def collect(self) -> List[RawNewsItem]:
        """Collect tweets from Twitter"""
        if not await self.authenticate():
            return []

        items = []

        try:
            # Search for recent tweets with Forex keywords
            query = " OR ".join(self.forex_keywords[:10])  # Limit to 10 keywords

            # Get tweets from the last hour
            start_time = datetime.utcnow() - timedelta(hours=1)

            tweets = self.client.search_recent_tweets(
                query=query,
                tweet_fields=["created_at", "author_id", "public_metrics", "entities"],
                user_fields=["username", "name"],
                expansions=["author_id"],
                max_results=100,
                start_time=start_time
            )

            if tweets.data:
                users = {u.id: u for u in tweets.includes["users"]} if tweets.includes else {}

                for tweet in tweets.data:
                    item = self.parse_tweet(tweet, users)
                    if item:
                        items.append(item)

        except Exception as e:
            print(f"Error collecting from Twitter: {e}")

        return items

    def parse_tweet(self, tweet: tweepy.Tweet, users: dict) -> Optional[RawNewsItem]:
        """Parse tweet from Twitter API response"""
        try:
            content = tweet.text

            # Remove URLs and mentions for cleaner analysis
            content = self.clean_tweet_text(content)

            # Extract currency pairs
            currency_pairs = self.extract_currency_pairs(content)

            # Get author info
            author_id = tweet.author_id
            author = users.get(author_id)
            author_name = author.username if author else "unknown"

            # Parse timestamp
            created_at = tweet.created_at
            if created_at:
                timestamp = created_at.replace(tzinfo=None)
            else:
                timestamp = datetime.utcnow()

            # Get engagement metrics
            public_metrics = tweet.public_metrics or {}

            return RawNewsItem(
                source=SourceType.TWITTER,
                source_id=str(tweet.id),
                content=content,
                title=None,  # Tweets don't have titles
                author=author_name,
                url=f"https://twitter.com/i/web/status/{tweet.id}",
                timestamp=timestamp,
                currency_pairs=currency_pairs,
                metadata={
                    "author_id": str(author_id),
                    "retweet_count": public_metrics.get("retweet_count", 0),
                    "like_count": public_metrics.get("like_count", 0),
                    "reply_count": public_metrics.get("reply_count", 0),
                    "quote_count": public_metrics.get("quote_count", 0)
                }
            )

        except Exception as e:
            print(f"Error parsing tweet: {e}")
            return None

    def clean_tweet_text(self, text: str) -> str:
        """Clean tweet text by removing URLs and mentions"""
        import re

        # Remove URLs
        text = re.sub(r'http\S+|www\.\S+', '', text)

        # Remove mentions
        text = re.sub(r'@\w+', '', text)

        # Remove hashtags (keep the text)
        text = re.sub(r'#(\w+)', r'\1', text)

        # Clean up whitespace
        text = " ".join(text.split())

        return text

    async def stream_tweets(self):
        """Stream tweets in real-time (optional feature)"""
        if not await self.authenticate():
            return

        try:
            # Create streaming client
            stream_client = tweepy.StreamingClient(
                bearer_token=self.bearer_token
            )

            # Add rules for Forex-related tweets
            rule = tweepy.StreamRule(" OR ".join(self.forex_keywords[:5]))
            stream_client.add_rules(rule)

            # Stream tweets
            for tweet in stream_client.filter(tweet_fields=["created_at", "author_id", "public_metrics"]):
                # Process tweet
                pass

        except Exception as e:
            print(f"Error streaming tweets: {e}")
