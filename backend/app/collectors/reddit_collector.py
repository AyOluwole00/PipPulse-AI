"""
Reddit Collector Module
Collects Forex-related posts from Reddit using PRAW
"""

from typing import List, Optional
from datetime import datetime, timedelta
import praw
import asyncio

from app.collectors.base import BaseCollector
from app.schemas import RawNewsItem, SourceType
from app.config import get_settings


class RedditCollector(BaseCollector):
    """Collector for Reddit API"""

    def __init__(self):
        super().__init__(SourceType.REDDIT)
        self.settings = get_settings()
        self.client_id = self.settings.reddit_client_id
        self.client_secret = self.settings.reddit_client_secret
        self.user_agent = self.settings.reddit_user_agent
        self.reddit: Optional[praw.Reddit] = None

        # Forex-related subreddits
        self.subreddits = self.settings.reddit_subreddits or [
            "Forex",
            "CurrencyTrading",
            "ForexStrategy",
            "Daytrading",
            "StockMarket"
        ]

        # Forex-related keywords
        self.forex_keywords = [
            "forex", "currency", "eur/usd", "gbp/usd", "usd/jpy",
            "dollar", "euro", "pound", "yen", "franc",
            "central bank", "federal reserve", "ecb", "boj"
        ]

    async def authenticate(self) -> bool:
        """Authenticate with Reddit API"""
        if not self.client_id or not self.client_secret:
            print("Reddit credentials not configured")
            return False

        try:
            # Create Reddit instance
            self.reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent=self.user_agent,
                read_only=True
            )

            # Test connection
            self.reddit.user.me()

            return True

        except Exception as e:
            print(f"Reddit authentication error: {e}")
            return False

    async def collect(self) -> List[RawNewsItem]:
        """Collect posts from Reddit"""
        if not await self.authenticate():
            return []

        items = []

        try:
            # Get posts from each subreddit
            for subreddit_name in self.subreddits:
                try:
                    subreddit = self.reddit.subreddit(subreddit_name)

                    # Get new posts from the last hour
                    for submission in subreddit.new(limit=50):
                        # Check if post is recent enough
                        post_time = datetime.fromtimestamp(submission.created_utc)
                        if datetime.utcnow() - post_time > timedelta(hours=1):
                            break

                        # Check if post contains Forex keywords
                        if not self._is_forex_related(submission):
                            continue

                        item = self.parse_submission(submission)
                        if item:
                            items.append(item)

                except Exception as e:
                    print(f"Error collecting from r/{subreddit_name}: {e}")
                    continue

        except Exception as e:
            print(f"Error collecting from Reddit: {e}")

        return items

    def _is_forex_related(self, submission) -> bool:
        """Check if a submission is Forex-related"""
        text = f"{submission.title} {submission.selftext}".lower()

        for keyword in self.forex_keywords:
            if keyword.lower() in text:
                return True

        return False

    def parse_submission(self, submission) -> Optional[RawNewsItem]:
        """Parse submission from Reddit API response"""
        try:
            # Get content
            if submission.selftext:
                content = submission.selftext
            else:
                content = submission.title

            # Clean content
            content = self.clean_reddit_text(content)

            # Extract currency pairs
            currency_pairs = self.extract_currency_pairs(content)

            # Parse timestamp
            timestamp = datetime.fromtimestamp(submission.created_utc)

            # Get author info
            author = submission.author.name if submission.author else "[deleted]"

            # Get engagement metrics
            upvotes = submission.score
            comments = submission.num_comments

            return RawNewsItem(
                source=SourceType.REDDIT,
                source_id=str(submission.id),
                content=content,
                title=submission.title,
                author=author,
                url=f"https://reddit.com{submission.permalink}",
                timestamp=timestamp,
                currency_pairs=currency_pairs,
                metadata={
                    "subreddit": str(submission.subreddit),
                    "upvotes": upvotes,
                    "comments": comments,
                    "is_self": submission.is_self
                }
            )

        except Exception as e:
            print(f"Error parsing submission: {e}")
            return None

    def clean_reddit_text(self, text: str) -> str:
        """Clean Reddit text by removing markdown and URLs"""
        import re

        # Remove URLs
        text = re.sub(r'http\S+|www\.\S+', '', text)

        # Remove markdown links
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)

        # Remove excessive whitespace
        text = " ".join(text.split())

        return text

    async def stream_submissions(self):
        """Stream submissions in real-time (optional feature)"""
        if not await self.authenticate():
            return

        try:
            for subreddit_name in self.subreddits:
                subreddit = self.reddit.subreddit(subreddit_name)

                for submission in subreddit.stream.submissions():
                    # Check if post is Forex-related
                    if not self._is_forex_related(submission):
                        continue

                    item = self.parse_submission(submission)
                    if item:
                        await self.publish_to_stream(item)

        except Exception as e:
            print(f"Error streaming submissions: {e}")
