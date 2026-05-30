"""
Synthetic News Generator for Latency Testing

Generates realistic synthetic news items for E2E latency testing
without requiring external news sources.
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict


# Sample financial news templates
TITLES = [
    "Apple Inc. reports record quarterly earnings",
    "Tesla stock surges on strong delivery numbers",
    "Federal Reserve cuts interest rates by 25 basis points",
    "Bitcoin reaches new all-time high",
    "Microsoft announces major cloud infrastructure investment",
    "JPMorgan upgrades tech sector outlook",
    "Gold prices spike amid geopolitical tensions",
    "Cryptocurrency market rallies on regulatory clarity",
    "Bank of England signals rate hike expectations",
    "Energy stocks decline on renewable energy push",
    "Oil prices fall on demand concerns",
    "Nasdaq reaches milestone 20,000 level",
    "Amazon expands AWS into new regions",
    "Meta invests $5 billion in AI infrastructure",
    "Nvidia reports chip shortage easing",
    "Semiconductor shortage impacting global supply chains",
    "Financial markets show strong earnings growth",
    "Inflation data comes in below expectations",
    "Stock market experiences minor pullback",
    "Healthcare stocks outperform market indices",
]

CONTENT_TEMPLATES = [
    "In today's market session, {noun} showed significant movement. "
    "Analysts suggest this reflects {sentiment_reason}. "
    "Market participants are closely watching developments in {sector}.",
    
    "{subject} announced {action} today, sending shares {direction} {percent}%. "
    "The move reflects investor {sentiment} regarding {outlook}.",
    
    "Trading in {ticker} intensified as new {news_type} emerged. "
    "Experts believe this could lead to {impact} in the {timeframe}.",
    
    "Financial markets responded positively to {event}. "
    "Industry analysts anticipate {consequence} for {sector} stocks.",
    
    "Economic data released today showed {metric} at {level}, "
    "exceeding expectations and signaling {implication} for the broader market.",
]

SUBJECTS = [
    "The technology sector", "Major financial institutions", "Growth stocks",
    "Value investors", "Cryptocurrency exchanges", "Banking sector",
    "Retail investors", "Energy companies", "Healthcare providers"
]

ACTIONS = [
    "launched a new product line",
    "reported earnings above estimates",
    "announced strategic partnerships",
    "expanded into new markets",
    "underwent leadership changes",
    "received regulatory approval",
    "completed a major acquisition",
    "announced dividend increases"
]

SENTIMENTS = [
    "optimistic", "bullish", "cautious", "bearish", "neutral", "positive"
]

SECTORS = [
    "technology", "finance", "energy", "healthcare", "retail", "manufacturing"
]


def generate_synthetic_items(count: int, interval_ms: int = 100) -> List[Dict]:
    """Generate synthetic news items for testing.
    
    Args:
        count: Number of items to generate
        interval_ms: Milliseconds between item timestamps
        
    Returns:
        List of news item dictionaries
    """
    items = []
    base_time = datetime.now() - timedelta(minutes=count * interval_ms / 1000 / 60)
    
    for i in range(count):
        timestamp = base_time + timedelta(milliseconds=i * interval_ms)
        
        title = random.choice(TITLES)
        subject = random.choice(SUBJECTS)
        action = random.choice(ACTIONS)
        sentiment = random.choice(SENTIMENTS)
        sector = random.choice(SECTORS)
        
        content = random.choice(CONTENT_TEMPLATES).format(
            noun=subject.lower(),
            sentiment_reason=sentiment + " market conditions",
            sector=sector,
            subject=subject,
            action=action,
            direction=random.choice(["up", "down"]),
            percent=random.randint(1, 10),
            sentiment=sentiment,
            outlook="strong recovery" if sentiment in ["optimistic", "bullish"] else "cautious growth",
            ticker=f"${random.choice(['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA'])}",
            news_type=random.choice(["earnings report", "market data", "regulatory news"]),
            impact="significant gains" if sentiment in ["optimistic", "bullish"] else "moderate losses",
            timeframe=random.choice(["coming weeks", "next quarter", "by year-end"]),
            event="positive market sentiment" if sentiment in ["optimistic", "bullish"] else "cautious outlook",
            consequence="upside momentum" if sentiment in ["optimistic", "bullish"] else "downside pressure",
            metric="GDP growth",
            level="2.5%",
            implication="economic strength",
        )
        
        items.append({
            "id": f"synthetic-{i:05d}",
            "title": title,
            "content": content,
            "source": random.choice(["Reuters", "Bloomberg", "MarketWatch", "CNBC", "Financial Times"]),
            "published_at": timestamp.isoformat(),
            "url": f"https://example.com/news/{i}",
            "tags": [sector, random.choice(["positive", "negative", "neutral"])],
        })
    
    return items


def generate_balanced_items(count: int, interval_ms: int = 100) -> List[Dict]:
    """Generate synthetic items with balanced sentiment distribution.
    
    Args:
        count: Total items to generate
        interval_ms: Milliseconds between item timestamps
        
    Returns:
        List of items with balanced positive/negative/neutral labels
    """
    items = generate_synthetic_items(count, interval_ms)
    
    # Assign balanced sentiments
    positive_count = count // 3
    neutral_count = count // 3
    negative_count = count - positive_count - neutral_count
    
    sentiments = ["positive"] * positive_count + ["neutral"] * neutral_count + ["negative"] * negative_count
    random.shuffle(sentiments)
    
    for item, sentiment in zip(items, sentiments):
        item["expected_sentiment"] = sentiment
    
    return items
