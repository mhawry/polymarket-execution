"""
Polymarket Execution Engine - High-speed order execution for prediction markets.

A Python library for automated trading on Polymarket prediction markets,
designed for speed, reliability, and safety.
"""

__version__ = "0.1.0"
__author__ = "Polymarket Execution Engine"

from .config import PolymarketConfig
from .trader import (
    OrderError,
    PolymarketTrader,
    TradingConnectionError,
    TradingError,
    ValidationError,
)

__all__ = [
    "PolymarketConfig",
    "PolymarketTrader",
    "ValidationError",
    "TradingConnectionError",
    "OrderError",
    "TradingError",
]
