"""
Strategy Engine Module - Trade Analysis
Handles historical analysis and trade strategy calculations
"""

from .trade_analyzer import TradeAnalyzer
from .backtest import BacktestEngine

__all__ = ['TradeAnalyzer', 'BacktestEngine'] 