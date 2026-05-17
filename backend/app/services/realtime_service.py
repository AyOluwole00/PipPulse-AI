"""
Redis pub/sub listener for realtime WebSocket broadcasts.
"""

import asyncio
import json
import logging
from typing import Optional

from app.database import get_redis
from app.api.websocket import broadcast_signal, broadcast_news

logger = logging.getLogger(__name__)


async def listen_for_events(stop_event: Optional[asyncio.Event] = None):
    """Listen to Redis pub/sub and forward messages to WebSocket clients."""
    redis = get_redis()
    if not redis:
        logger.error("Redis not available for realtime listener")
        return

    pubsub = redis.pubsub()
    await pubsub.subscribe("signals", "news")
    logger.info("Realtime listener subscribed to Redis channels: signals, news")

    try:
        async for message in pubsub.listen():
            if stop_event and stop_event.is_set():
                break

            if message.get("type") != "message":
                continue

            channel = message.get("channel")
            payload = message.get("data")
            if isinstance(payload, bytes):
                payload = payload.decode()

            try:
                data = json.loads(payload) if isinstance(payload, str) else payload
            except json.JSONDecodeError:
                logger.warning("Invalid JSON payload received on realtime channel")
                continue

            if channel in ("signals", b"signals"):
                await broadcast_signal(data)
            elif channel in ("news", b"news"):
                await broadcast_news(data)
    except asyncio.CancelledError:
        logger.info("Realtime listener cancelled")
    finally:
        await pubsub.close()
