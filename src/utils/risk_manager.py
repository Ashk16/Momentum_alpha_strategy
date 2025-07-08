"""
Risk Manager
Handles risk management and pre-trade checks
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta

from .logger import get_logger


class RiskManager:
    """Manages trading risk and performs pre-trade checks."""
    
    def __init__(self, config: Dict):
        """
        Initialize risk manager.
        
        Args:
            config: Risk management configuration
        """
        self.config = config
        self.logger = get_logger(__name__)
        
        # Risk limits
        self.max_position_size = config.get('max_position_size', 50000)
        self.max_daily_trades = config.get('max_daily_trades', 5)
        self.max_weekly_trades = config.get('max_weekly_trades', 20)
        self.risk_per_trade = config.get('risk_per_trade', 0.02)
        self.max_portfolio_risk = config.get('max_portfolio_risk', 0.10)
        self.circuit_breaker_threshold = config.get('circuit_breaker_threshold', 0.05)
        self.vix_threshold = config.get('vix_threshold', 25)
        
        # Track daily statistics
        self.daily_trades = 0
        self.daily_pnl = 0.0
        self.last_reset_date = datetime.now().date()
        
        self.logger.info("Risk Manager initialized")
    
    def pre_trade_check(self, processed_data: Dict) -> bool:
        """
        Perform pre-trade risk checks.
        
        Args:
            processed_data: Processed announcement data
            
        Returns:
            True if trade is allowed, False otherwise
        """
        try:
            # Reset daily counters if new day
            self._reset_daily_counters_if_needed()
            
            # Check all risk conditions
            checks = [
                self._check_daily_trade_limit(),
                self._check_position_size_limit(processed_data),
                self._check_market_conditions(),
                self._check_portfolio_risk(),
                self._check_confidence_threshold(processed_data)
            ]
            
            all_passed = all(checks)
            
            if all_passed:
                self.logger.info(f"Pre-trade checks passed for {processed_data.get('symbol', 'UNKNOWN')}")
            else:
                self.logger.warning(f"Pre-trade checks failed for {processed_data.get('symbol', 'UNKNOWN')}")
            
            return all_passed
            
        except Exception as e:
            self.logger.error(f"Error in pre-trade check: {e}")
            return False
    
    def _reset_daily_counters_if_needed(self):
        """Reset daily counters if it's a new day."""
        current_date = datetime.now().date()
        if current_date != self.last_reset_date:
            self.daily_trades = 0
            self.daily_pnl = 0.0
            self.last_reset_date = current_date
            self.logger.info("Daily counters reset")
    
    def _check_daily_trade_limit(self) -> bool:
        """Check if daily trade limit is exceeded."""
        if self.daily_trades >= self.max_daily_trades:
            self.logger.warning(f"Daily trade limit exceeded: {self.daily_trades}/{self.max_daily_trades}")
            return False
        return True
    
    def _check_position_size_limit(self, processed_data: Dict) -> bool:
        """Check position size limits."""
        order_value = processed_data.get('order_value', 0)
        
        # Check maximum position size
        if order_value > self.max_position_size:
            self.logger.warning(f"Position size {order_value} exceeds limit {self.max_position_size}")
            return False
        
        return True
    
    def _check_market_conditions(self) -> bool:
        """Check overall market conditions."""
        # In production, integrate with market data to check:
        # - India VIX levels
        # - Market circuit breakers
        # - Trading halts
        
        # Stub implementation
        current_hour = datetime.now().hour
        
        # Check trading hours (approximate)
        if current_hour < 9 or current_hour > 15:
            self.logger.warning("Outside trading hours")
            return False
        
        # Check if it's a weekend
        if datetime.now().weekday() >= 5:  # Saturday=5, Sunday=6
            self.logger.warning("Weekend - markets closed")
            return False
        
        return True
    
    def _check_portfolio_risk(self) -> bool:
        """Check overall portfolio risk."""
        # Check daily loss limit
        if self.daily_pnl < -self.circuit_breaker_threshold * self.max_position_size:
            self.logger.warning(f"Daily loss limit exceeded: {self.daily_pnl}")
            return False
        
        return True
    
    def _check_confidence_threshold(self, processed_data: Dict) -> bool:
        """Check if confidence meets minimum threshold."""
        confidence = processed_data.get('confidence', 0.0)
        min_confidence = 0.7  # Minimum confidence for trading
        
        if confidence < min_confidence:
            self.logger.warning(f"Confidence {confidence} below minimum {min_confidence}")
            return False
        
        return True
    
    def record_trade(self, trade_result: Dict):
        """
        Record a completed trade for risk tracking.
        
        Args:
            trade_result: Trade result dictionary
        """
        try:
            self.daily_trades += 1
            pnl = trade_result.get('profit_loss', 0.0)
            self.daily_pnl += pnl
            
            self.logger.info(f"Trade recorded - Daily trades: {self.daily_trades}, Daily PnL: {self.daily_pnl}")
            
        except Exception as e:
            self.logger.error(f"Error recording trade: {e}")
    
    def get_risk_status(self) -> Dict:
        """
        Get current risk status.
        
        Returns:
            Risk status dictionary
        """
        return {
            'daily_trades': self.daily_trades,
            'daily_trades_remaining': max(0, self.max_daily_trades - self.daily_trades),
            'daily_pnl': self.daily_pnl,
            'daily_loss_limit': -self.circuit_breaker_threshold * self.max_position_size,
            'risk_capacity_used': abs(self.daily_pnl) / (self.circuit_breaker_threshold * self.max_position_size),
            'last_reset_date': self.last_reset_date.isoformat()
        }
    
    def emergency_stop(self) -> bool:
        """
        Emergency stop all trading.
        
        Returns:
            True if emergency stop activated
        """
        self.logger.critical("EMERGENCY STOP ACTIVATED")
        # Set daily trades to maximum to prevent further trading
        self.daily_trades = self.max_daily_trades
        return True 