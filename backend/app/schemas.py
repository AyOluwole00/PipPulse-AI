"""
Data Models and Schemas
Defines the structure of data entities in the system
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, HttpUrl


class SourceType(str, Enum):
    """Data source types"""
    NEWSAPI = "newsapi"
    TWITTER = "twitter"
    REDDIT = "reddit"
    TELEGRAM = "telegram"


class SentimentLabel(str, Enum):
    """Sentiment classification labels"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class SignalDirection(str, Enum):
    """Trading signal directions"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class CurrencyPair(str, Enum):
    """Major currency pairs"""
    EUR_USD = "EUR/USD"
    GBP_USD = "GBP/USD"
    USD_JPY = "USD/JPY"
    USD_CHF = "USD/CHF"
    AUD_USD = "AUD/USD"
    USD_CAD = "USD/CAD"
    NZD_USD = "NZD/USD"
    USD_SGD = "USD/SGD"


# Raw News Item Schema
class RawNewsItem(BaseModel):
    """Raw news item from any source"""
    source: SourceType
    source_id: str  # Unique ID from the source platform
    content: str
    title: Optional[str] = None
    author: Optional[str] = None
    url: Optional[HttpUrl] = None
    timestamp: datetime
    currency_pairs: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    content_hash: Optional[str] = None  # For deduplication

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Processed News Item Schema
class ProcessedNewsItem(BaseModel):
    """Processed news item after cleaning and NLP"""
    source: SourceType
    source_id: str
    original_content: str
    cleaned_content: str
    title: Optional[str] = None
    author: Optional[str] = None
    url: Optional[HttpUrl] = None
    timestamp: datetime
    currency_pairs: List[str] = Field(default_factory=list)
    language: str = "en"
    is_spam: bool = False
    is_bot: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)
    content_hash: str

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Sentiment Result Schema
class SentimentResult(BaseModel):
    """Sentiment analysis result"""
    content_hash: str
    label: SentimentLabel
    confidence: float = Field(ge=0.0, le=1.0)
    probabilities: Dict[str, float] = Field(default_factory=dict)
    timestamp: datetime
    model_name: str = "ProsusAI/finbert"
    pair_sentiment: Dict[str, float] = Field(default_factory=dict)  # Sentiment per currency pair

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Signal Schema
class TradingSignal(BaseModel):
    """Trading signal generated from sentiment analysis"""
    currency_pair: str
    direction: SignalDirection
    strength: float = Field(ge=0.0, le=100.0)  # Signal strength 0-100
    confidence: float = Field(ge=0.0, le=100.0)  # Confidence score 0-100
    timestamp: datetime
    time_window: str  # "15min", "1hour", "4hour"
    reference_price: Optional[float] = None
    supporting_headlines: List[str] = Field(default_factory=list)
    reasoning: str
    sentiment_score: float = Field(ge=-1.0, le=1.0)
    volume: int = Field(default=0)  # Number of news items
    consensus_factor: float = Field(ge=0.0, le=1.0)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# API Response Schemas
class SignalResponse(BaseModel):
    """API response for trading signals"""
    currency_pair: str
    direction: SignalDirection
    strength: float
    confidence: float
    timestamp: datetime
    time_window: str
    reasoning: str
    supporting_headlines: List[str]
    sentiment_score: float = Field(ge=-1.0, le=1.0, default=0.0)
    volume: int = 0
    consensus_factor: float = Field(ge=0.0, le=1.0, default=0.0)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SentimentTrend(BaseModel):
    """Sentiment trend data for visualization"""
    currency_pair: str
    timestamps: List[datetime]
    sentiment_scores: List[float]
    signal_counts: List[int]

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class NewsItemResponse(BaseModel):
    """API response for news items"""
    source: SourceType
    title: Optional[str]
    content: str
    url: Optional[HttpUrl]
    timestamp: datetime
    currency_pairs: List[str]
    sentiment: Optional[SentimentResult] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Backtest Result Schema
class BacktestResult(BaseModel):
    """Backtesting results"""
    currency_pair: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    total_return: float
    win_rate: float
    average_risk_reward: float
    sharpe_ratio: float
    max_drawdown: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    confidence_calibration: Dict[str, float] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Configuration Schemas
class SignalConfig(BaseModel):
    """Signal generation configuration"""
    currency_pair: str
    buy_threshold: float = Field(default=0.3, ge=0.0, le=1.0)
    sell_threshold: float = Field(default=-0.3, ge=-1.0, le=0.0)
    confidence_threshold: float = Field(default=0.6, ge=0.0, le=1.0)
    time_decay_lambda: float = Field(default=0.1, ge=0.0)


class SourceWeightConfig(BaseModel):
    """Source credibility weight configuration"""
    source: SourceType
    weight: float = Field(ge=0.0, le=1.0)


class WindowConfig(BaseModel):
    """Time window configuration"""
    name: str
    minutes: int


# API Key Management Schema
class APIKeyConfig(BaseModel):
    """API key configuration"""
    service: str
    key: str
    is_active: bool = True
    last_used: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# WebSocket Message Schemas
class WebSocketMessage(BaseModel):
    """WebSocket message structure"""
    type: str  # "signal", "news", "error", "heartbeat"
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Error Response Schema
class ErrorResponse(BaseModel):
    """Error response structure"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
