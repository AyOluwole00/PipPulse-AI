"""
Telegram Collector Module
Collects Forex-related messages from Telegram using Telethon
"""

from typing import List, Optional
from datetime import datetime, timedelta
from telethon import TelegramClient, events
from telethon.tl.types import Message
import asyncio

from app.collectors.base import BaseCollector
from app.schemas import RawNewsItem, SourceType
from app.config import get_settings


class TelegramCollector(BaseCollector):
    """Collector for Telegram API"""

    def __init__(self):
        super().__init__(SourceType.TELEGRAM)
        self.settings = get_settings()
        self.api_id = self.settings.telegram_api_id
        self.api_hash = self.settings.telegram_api_hash
        self.bot_token = self.settings.telegram_bot_token
        self.client: Optional[TelegramClient] = None

        # Forex-related channels
        self.channels = self.settings.telegram_channels or [
            "forex_signals",
            "forex_trading"
        ]

        # Forex-related keywords
        self.forex_keywords = [
            "forex", "currency", "eur/usd", "gbp/usd", "usd/jpy",
            "dollar", "euro", "pound", "yen", "franc",
            "central bank", "federal reserve", "ecb", "boj"
        ]

    async def authenticate(self) -> bool:
        """Authenticate with Telegram API"""
        if not self.api_id or not self.api_hash:
            print("Telegram credentials not configured")
            return False

        try:
            # Create Telegram client
            self.client = TelegramClient(
                'pippulse_telegram',
                self.api_id,
                self.api_hash
            )

            # Connect to Telegram
            await self.client.connect()

            # Check if already authorized
            if not await self.client.is_user_authorized():
                print("Telegram client not authorized. Please run the authentication script first.")
                return False

            return True

        except Exception as e:
            print(f"Telegram authentication error: {e}")
            return False

    async def collect(self) -> List[RawNewsItem]:
        """Collect messages from Telegram"""
        if not await self.authenticate():
            return []

        items = []

        try:
            # Get messages from each channel
            for channel_name in self.channels:
                try:
                    # Get channel entity
                    channel = await self.client.get_entity(channel_name)

                    # Get messages from the last hour
                    start_time = datetime.utcnow() - timedelta(hours=1)

                    async for message in self.client.iter_messages(
                        channel,
                        limit=100
                    ):
                        # Check if message is recent enough
                        if message.date < start_time:
                            break

                        # Check if message contains Forex keywords
                        if not self._is_forex_related(message):
                            continue

                        item = self.parse_message(message, channel_name)
                        if item:
                            items.append(item)

                except Exception as e:
                    print(f"Error collecting from channel {channel_name}: {e}")
                    continue

        except Exception as e:
            print(f"Error collecting from Telegram: {e}")

        return items

    def _is_forex_related(self, message: Message) -> bool:
        """Check if a message is Forex-related"""
        text = ""

        if message.text:
            text += message.text + " "

        if message.message:
            text += str(message.message) + " "

        text = text.lower()

        for keyword in self.forex_keywords:
            if keyword.lower() in text:
                return True

        return False

    def parse_message(self, message: Message, channel_name: str) -> Optional[RawNewsItem]:
        """Parse message from Telegram API response"""
        try:
            # Get content
            content = message.text or str(message.message) if message.message else ""

            # Clean content
            content = self.clean_telegram_text(content)

            # Extract currency pairs
            currency_pairs = self.extract_currency_pairs(content)

            # Parse timestamp
            timestamp = message.date

            # Get author info
            author = None
            if message.sender:
                author = getattr(message.sender, 'username', None) or getattr(message.sender, 'first_name', None)

            # Get engagement metrics
            views = getattr(message, 'views', 0)
            forwards = getattr(message, 'forwards', 0)

            return RawNewsItem(
                source=SourceType.TELEGRAM,
                source_id=str(message.id),
                content=content,
                title=None,  # Telegram messages don't have titles
                author=author,
                url=f"https://t.me/{channel_name}/{message.id}",
                timestamp=timestamp,
                currency_pairs=currency_pairs,
                metadata={
                    "channel": channel_name,
                    "views": views,
                    "forwards": forwards,
                    "reply_to_msg_id": message.reply_to_msg_id if message.reply_to else None
                }
            )

        except Exception as e:
            print(f"Error parsing message: {e}")
            return None

    def clean_telegram_text(self, text: str) -> str:
        """Clean Telegram text by removing formatting"""
        import re

        # Remove URLs
        text = re.sub(r'http\S+|www\.\S+', '', text)

        # Remove mentions
        text = re.sub(r'@\w+', '', text)

        # Remove excessive whitespace
        text = " ".join(text.split())

        return text

    async def stream_messages(self):
        """Stream messages in real-time (optional feature)"""
        if not await self.authenticate():
            return

        try:
            @self.client.on(events.NewMessage)
            async def handler(event):
                message = event.message

                # Check if message is Forex-related
                if not self._is_forex_related(message):
                    return

                # Get channel name
                chat = await event.get_chat()
                channel_name = getattr(chat, 'username', None) or getattr(chat, 'title', 'unknown')

                item = self.parse_message(message, channel_name)
                if item:
                    await self.publish_to_stream(item)

            # Run the client
            await self.client.run_until_disconnected()

        except Exception as e:
            print(f"Error streaming messages: {e}")

    async def disconnect(self):
        """Disconnect from Telegram"""
        if self.client:
            await self.client.disconnect()
