"""
Latency Tracking Infrastructure for PipPulse AI

Tracks end-to-end latency across the sentiment analysis pipeline:
- News collection → Preprocessing → Sentiment inference → Signal generation → WebSocket delivery

Usage:
    tracker = LatencyTracker("news-item-001")
    tracker.record_event("collection_start")
    tracker.record_event("collection_end")
    tracker.record_event("sentiment_end")
    total_latency = tracker.get_total_latency()  # ms
    tracker.save_to_file("latency_data.json")
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


class LatencyTracker:
    """Tracks latency measurements across pipeline components."""

    def __init__(self, item_id: str):
        """Initialize tracker for a news item.
        
        Args:
            item_id: Unique identifier for the news item being tracked
        """
        self.item_id = item_id
        self.events: Dict[str, float] = {}  # event_name -> timestamp (milliseconds)
        self.start_time = time.time() * 1000  # Convert to ms
        
    def record_event(self, event_name: str) -> None:
        """Record a timestamp for an event.
        
        Args:
            event_name: Name of the event (e.g., "collection_start", "sentiment_end")
        """
        timestamp = time.time() * 1000  # Convert to milliseconds
        self.events[event_name] = timestamp
    
    def calculate_latency(self, start_event: str, end_event: str) -> float:
        """Calculate latency between two events.
        
        Args:
            start_event: Name of the start event
            end_event: Name of the end event
            
        Returns:
            Latency in milliseconds, or -1 if events don't exist
        """
        if start_event not in self.events or end_event not in self.events:
            return -1.0
        return self.events[end_event] - self.events[start_event]
    
    def get_total_latency(self) -> float:
        """Get total latency from first to last recorded event.
        
        Returns:
            Total latency in milliseconds
        """
        if not self.events:
            return 0.0
        
        timestamps = list(self.events.values())
        return max(timestamps) - min(timestamps)
    
    def get_component_latencies(self) -> Dict[str, float]:
        """Get latencies for each pipeline component.
        
        Returns:
            Dictionary mapping component -> latency_ms
        """
        component_pairs = [
            ("collection_start", "collection_end", "collection"),
            ("collection_end", "preprocessing_end", "preprocessing"),
            ("preprocessing_end", "sentiment_end", "sentiment"),
            ("sentiment_end", "signal_end", "signal"),
            ("signal_end", "websocket_delivery", "delivery"),
        ]
        
        latencies = {}
        for start, end, name in component_pairs:
            latency = self.calculate_latency(start, end)
            if latency >= 0:
                latencies[name] = latency
        
        return latencies
    
    def to_dict(self) -> Dict[str, object]:
        """Export all latencies to dictionary.
        
        Returns:
            Dictionary with item_id, events, component latencies, and total latency
        """
        return {
            "item_id": self.item_id,
            "timestamp": datetime.now().isoformat(),
            "events": {k: v for k, v in self.events.items()},
            "component_latencies_ms": self.get_component_latencies(),
            "total_latency_ms": self.get_total_latency(),
        }
    
    def save_to_file(self, filepath: str) -> None:
        """Save latency data to JSON file.
        
        Args:
            filepath: Path where to save the JSON file
        """
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)


class LatencyAggregator:
    """Aggregates latency measurements across multiple items."""
    
    def __init__(self):
        """Initialize aggregator."""
        self.trackers: Dict[str, LatencyTracker] = {}
    
    def add_tracker(self, tracker: LatencyTracker) -> None:
        """Add a tracker to the aggregator.
        
        Args:
            tracker: LatencyTracker instance
        """
        self.trackers[tracker.item_id] = tracker
    
    def get_percentile(self, percentile: float) -> float:
        """Get latency at given percentile.
        
        Args:
            percentile: Percentile (0-100)
            
        Returns:
            Latency in milliseconds at given percentile
        """
        if not self.trackers:
            return 0.0
        
        latencies = sorted([t.get_total_latency() for t in self.trackers.values()])
        idx = int(len(latencies) * percentile / 100)
        return latencies[min(idx, len(latencies) - 1)]
    
    def get_statistics(self) -> Dict[str, float]:
        """Calculate latency statistics.
        
        Returns:
            Dictionary with P50, P95, P99, min, max, and average latencies
        """
        if not self.trackers:
            return {}
        
        latencies = [t.get_total_latency() for t in self.trackers.values()]
        
        return {
            "count": len(latencies),
            "min_ms": min(latencies),
            "max_ms": max(latencies),
            "avg_ms": sum(latencies) / len(latencies),
            "p50_ms": self.get_percentile(50),
            "p95_ms": self.get_percentile(95),
            "p99_ms": self.get_percentile(99),
        }
    
    def get_component_statistics(self) -> Dict[str, Dict[str, float]]:
        """Get statistics for each pipeline component.
        
        Returns:
            Dictionary mapping component -> statistics
        """
        component_latencies: Dict[str, list] = {}
        
        for tracker in self.trackers.values():
            for component, latency in tracker.get_component_latencies().items():
                if component not in component_latencies:
                    component_latencies[component] = []
                component_latencies[component].append(latency)
        
        stats = {}
        for component, latencies in component_latencies.items():
            stats[component] = {
                "count": len(latencies),
                "min_ms": min(latencies),
                "max_ms": max(latencies),
                "avg_ms": sum(latencies) / len(latencies),
            }
        
        return stats
    
    def save_report(self, filepath: str) -> None:
        """Save comprehensive latency report to JSON.
        
        Args:
            filepath: Path where to save the report
        """
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": self.get_statistics(),
            "component_statistics": self.get_component_statistics(),
            "individual_items": [t.to_dict() for t in self.trackers.values()],
        }
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
