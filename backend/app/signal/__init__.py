"""
Signal Module
Generates BUY/SELL/HOLD trading signals from sentiment analysis
"""

from app.signal.generator import (
    SignalGenerator,
    SignalAggregator,
    TimeDecayCalculator,
    SourceCredibilityWeighter,
    ConsensusCalculator,
    SignalStrengthCalculator,
    ExplainabilityBuilder,
    TimeWindow,
    SourceWeight,
    SignalConfig
)

__all__ = [
    "SignalGenerator",
    "SignalAggregator",
    "TimeDecayCalculator",
    "SourceCredibilityWeighter",
    "ConsensusCalculator",
    "SignalStrengthCalculator",
    "ExplainabilityBuilder",
    "TimeWindow",
    "SourceWeight",
    "SignalConfig"
]
