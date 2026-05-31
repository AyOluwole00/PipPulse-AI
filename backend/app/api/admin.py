"""
Admin Configuration API Endpoints

Provides REST API for managing PipPulse AI system configuration:
- Signal thresholds by currency pair
- Source credibility weights
- Time window settings
- Confidence thresholds
- System health metrics

Security: All endpoints should be protected by authentication middleware.
"""

import os
import psutil
from datetime import datetime
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])

# System startup time (for uptime calculation)
STARTUP_TIME = datetime.now()

# In-memory configuration storage (replace with database in production)
CONFIG = {
    "signal_thresholds": {
        "EUR/USD": {"buy": 60, "sell": 40, "hold": 50},
        "GBP/USD": {"buy": 60, "sell": 40, "hold": 50},
        "USD/JPY": {"buy": 60, "sell": 40, "hold": 50},
    },
    "source_weights": {
        "newsapi": 1.0,
        "twitter": 1.2,
        "reddit": 0.8,
        "telegram": 0.6,
    },
    "time_windows": [900, 3600, 14400],  # 15m, 1h, 4h
    "confidence_threshold": 0.5,
}


class ThresholdUpdate(BaseModel):
    """Signal threshold update request."""
    pair: str = Field(..., example="EUR/USD")
    buy_threshold: int = Field(..., ge=0, le=100, example=60)
    sell_threshold: int = Field(..., ge=0, le=100, example=40)


class WeightUpdate(BaseModel):
    """Source weight update request."""
    source: str = Field(..., example="newsapi")
    weight: float = Field(..., ge=0.5, le=2.0, example=1.0)


class WindowsUpdate(BaseModel):
    """Time windows update request."""
    windows: List[int] = Field(..., example=[900, 3600, 14400])


def get_system_stats() -> Dict[str, Any]:
    """Get current system resource statistics."""
    try:
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        cpu_percent = process.cpu_percent(interval=0.1)
        
        # Calculate uptime
        uptime = (datetime.now() - STARTUP_TIME).total_seconds()
        
        # Get total system memory for percentage calculation
        total_memory = psutil.virtual_memory().total
        memory_percent = (memory_info.rss / total_memory) * 100
        
        # Determine health status
        status = "healthy"
        if cpu_percent > 75 or memory_percent > 80:
            status = "degraded"
        elif cpu_percent > 90 or memory_percent > 95:
            status = "unhealthy"
        
        return {
            "cpu_percent": cpu_percent,
            "memory_mb": memory_info.rss / 1024 / 1024,
            "memory_percent": memory_percent,
            "uptime_seconds": int(uptime),
            "status": status,
            "last_update": datetime.now().isoformat()
        }
    except Exception as e:
        logger.warning(f"Failed to collect system stats: {e}")
        return {
            "cpu_percent": 0,
            "memory_mb": 0,
            "memory_percent": 0,
            "uptime_seconds": 0,
            "status": "unknown",
            "last_update": datetime.now().isoformat()
        }


@router.get("/config")
async def get_config() -> Dict[str, Any]:
    """
    Get all current system configuration.
    
    Returns:
        Current configuration including thresholds, weights, windows, and confidence threshold
    """
    return {
        "signal_thresholds": CONFIG["signal_thresholds"],
        "source_weights": CONFIG["source_weights"],
        "time_windows": CONFIG["time_windows"],
        "confidence_threshold": CONFIG["confidence_threshold"],
    }


@router.post("/config/thresholds")
async def update_thresholds(update: ThresholdUpdate) -> Dict[str, Any]:
    """
    Update signal thresholds for a currency pair.
    
    Args:
        update: ThresholdUpdate with pair, buy_threshold, sell_threshold
        
    Returns:
        Updated configuration for the currency pair
        
    Raises:
        HTTPException: If pair not found or invalid thresholds
    """
    pair = update.pair.upper()
    
    # Validate pair
    if pair not in CONFIG["signal_thresholds"]:
        raise HTTPException(
            status_code=400,
            detail=f"Currency pair '{pair}' not found. Available: {list(CONFIG['signal_thresholds'].keys())}"
        )
    
    # Validate thresholds
    if update.buy_threshold <= update.sell_threshold:
        raise HTTPException(
            status_code=400,
            detail="BUY threshold must be greater than SELL threshold"
        )
    
    # Update configuration
    CONFIG["signal_thresholds"][pair]["buy"] = update.buy_threshold
    CONFIG["signal_thresholds"][pair]["sell"] = update.sell_threshold
    
    logger.info(f"Updated thresholds for {pair}: BUY={update.buy_threshold}, SELL={update.sell_threshold}")
    
    return {
        "pair": pair,
        "thresholds": CONFIG["signal_thresholds"][pair],
        "message": f"Thresholds updated for {pair}"
    }


@router.post("/config/weights")
async def update_weights(update: WeightUpdate) -> Dict[str, Any]:
    """
    Update credibility weight for a news source.
    
    Args:
        update: WeightUpdate with source and weight (0.5-2.0)
        
    Returns:
        Updated weight configuration
        
    Raises:
        HTTPException: If source not found
    """
    source = update.source.lower()
    
    # Validate source
    if source not in CONFIG["source_weights"]:
        raise HTTPException(
            status_code=400,
            detail=f"Source '{source}' not found. Available: {list(CONFIG['source_weights'].keys())}"
        )
    
    # Update configuration
    CONFIG["source_weights"][source] = update.weight
    
    logger.info(f"Updated weight for {source}: {update.weight}")
    
    return {
        "source": source,
        "weight": update.weight,
        "message": f"Weight updated for {source}",
        "all_weights": CONFIG["source_weights"]
    }


@router.post("/config/windows")
async def update_windows(update: WindowsUpdate) -> Dict[str, Any]:
    """
    Update time window configuration.
    
    Args:
        update: WindowsUpdate with list of windows in seconds
        
    Returns:
        Updated windows configuration
        
    Raises:
        HTTPException: If windows are invalid
    """
    # Validate windows
    if not update.windows or len(update.windows) == 0:
        raise HTTPException(
            status_code=400,
            detail="At least one time window is required"
        )
    
    if any(w <= 0 for w in update.windows):
        raise HTTPException(
            status_code=400,
            detail="All time windows must be positive integers (seconds)"
        )
    
    # Windows should be in ascending order
    if update.windows != sorted(update.windows):
        raise HTTPException(
            status_code=400,
            detail="Time windows must be in ascending order"
        )
    
    # Update configuration
    CONFIG["time_windows"] = update.windows
    
    logger.info(f"Updated time windows: {update.windows}")
    
    return {
        "windows": update.windows,
        "windows_formatted": [f"{w//60}m" if w % 60 == 0 else f"{w}s" for w in update.windows],
        "message": "Time windows updated successfully"
    }


@router.get("/config/pairs")
async def get_pairs() -> Dict[str, List[str]]:
    """Get list of available currency pairs."""
    return {
        "pairs": list(CONFIG["signal_thresholds"].keys())
    }


@router.get("/config/sources")
async def get_sources() -> Dict[str, List[str]]:
    """Get list of available news sources."""
    return {
        "sources": list(CONFIG["source_weights"].keys())
    }


@router.get("/health")
async def health() -> Dict[str, Any]:
    """
    Health check endpoint with system metrics.
    
    Returns:
        System status and resource metrics
    """
    stats = get_system_stats()
    return {
        "status": stats["status"],
        "service": "admin-api",
        **stats
    }
