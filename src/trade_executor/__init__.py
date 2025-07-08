"""
Trade Executor Module - Order Management
Handles trade execution and broker API integration
"""

from .order_manager import OrderManager
from .broker_interface import BrokerInterface

__all__ = ['OrderManager', 'BrokerInterface'] 