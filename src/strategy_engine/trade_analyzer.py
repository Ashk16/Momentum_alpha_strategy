"""
Trade Analyzer - Strategy Engine
Analyzes historical data and generates trading signals
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta

from ..utils.logger import get_logger


class TradeAnalyzer:
    """Analyzes trade opportunities based on historical data and strategy."""
    
    def __init__(self, config: Dict, db_manager):
        """
        Initialize trade analyzer.
        
        Args:
            config: Strategy configuration dictionary
            db_manager: Database manager instance
        """
        self.config = config
        self.db_manager = db_manager
        self.logger = get_logger(__name__)
        
        self.lookback_days = config.get('lookback_days', 30)
        self.min_historical_data_points = config.get('min_historical_data_points', 10)
        self.target_multiplier = config.get('target_multiplier', 0.9)
        self.volatility_multiplier = config.get('volatility_multiplier', 2.0)
        self.max_holding_period = config.get('max_holding_period', 5)
        
        self.logger.info("Trade Analyzer initialized")
    
    async def analyze_trade_opportunity(self, processed_data: Dict) -> Dict:
        """
        Analyze a trade opportunity based on processed announcement data.
        
        Args:
            processed_data: Processed announcement data from NLP engine
            
        Returns:
            Trade signal dictionary
        """
        try:
            symbol = processed_data.get('symbol', '')
            order_value = processed_data.get('order_value')
            confidence = processed_data.get('confidence', 0.0)
            
            # Basic validation
            if not symbol:
                return self._create_signal(False, "No symbol identified")
            
            # Get historical data
            historical_data = await self._get_historical_performance(symbol)
            
            # Analyze historical performance
            analysis_result = self._analyze_historical_performance(historical_data, order_value)
            
            # Generate trading signal
            signal = self._generate_trading_signal(
                symbol, processed_data, analysis_result
            )
            
            self.logger.debug(f"Trade analysis completed for {symbol}: {signal['should_trade']}")
            return signal
            
        except Exception as e:
            self.logger.error(f"Error analyzing trade opportunity: {e}")
            return self._create_signal(False, f"Analysis error: {e}")
    
    async def _get_historical_performance(self, symbol: str) -> List[Dict]:
        """
        Get historical performance data for similar announcements.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            List of historical trade data
        """
        try:
            # Get historical trades for this symbol
            historical_trades = await self.db_manager.get_historical_trades(
                symbol=symbol, 
                days=self.lookback_days
            )
            
            return historical_trades
            
        except Exception as e:
            self.logger.error(f"Error getting historical data for {symbol}: {e}")
            return []
    
    def _analyze_historical_performance(self, historical_data: List[Dict], order_value: Optional[float]) -> Dict:
        """
        Analyze historical performance to determine strategy parameters.
        
        Args:
            historical_data: Historical trade data
            order_value: Current order value
            
        Returns:
            Analysis results dictionary
        """
        if not historical_data or len(historical_data) < self.min_historical_data_points:
            # No sufficient historical data - use default strategy
            return self._default_strategy_params(order_value)
        
        # Calculate performance metrics
        profits = []
        losses = []
        holding_periods = []
        
        for trade in historical_data:
            pnl = trade.get('profit_loss', 0)
            if pnl > 0:
                profits.append(pnl)
            elif pnl < 0:
                losses.append(abs(pnl))
            
            # Calculate holding period
            entry_time = trade.get('entry_time')
            exit_time = trade.get('exit_time')
            if entry_time and exit_time:
                holding_period = (exit_time - entry_time).days
                holding_periods.append(holding_period)
        
        # Calculate metrics
        total_trades = len(historical_data)
        winning_trades = len(profits)
        losing_trades = len(losses)
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        avg_profit = sum(profits) / len(profits) if profits else 0
        avg_loss = sum(losses) / len(losses) if losses else 0
        avg_holding_period = sum(holding_periods) / len(holding_periods) if holding_periods else 1
        
        return {
            'has_historical_data': True,
            'total_trades': total_trades,
            'win_rate': win_rate,
            'avg_profit': avg_profit,
            'avg_loss': avg_loss,
            'avg_holding_period': avg_holding_period,
            'recommendation': 'PROCEED' if win_rate > 0.6 else 'CAUTION'
        }
    
    def _default_strategy_params(self, order_value: Optional[float]) -> Dict:
        """
        Generate default strategy parameters when no historical data is available.
        
        Args:
            order_value: Order value
            
        Returns:
            Default strategy parameters
        """
        # Conservative default parameters
        base_target = 0.05  # 5% target
        base_stop_loss = 0.02  # 2% stop loss
        
        # Adjust based on order value
        if order_value:
            if order_value > 500000000:  # > 50 crores
                base_target *= 1.2  # Higher target for larger orders
            elif order_value < 50000000:  # < 5 crores
                base_target *= 0.8  # Lower target for smaller orders
        
        return {
            'has_historical_data': False,
            'target_percentage': base_target,
            'stop_loss_percentage': base_stop_loss,
            'recommended_holding_period': 3,
            'recommendation': 'PROCEED_CAUTIOUSLY'
        }
    
    def _generate_trading_signal(self, symbol: str, processed_data: Dict, analysis_result: Dict) -> Dict:
        """
        Generate final trading signal based on analysis.
        
        Args:
            symbol: Stock symbol
            processed_data: Processed announcement data
            analysis_result: Historical analysis result
            
        Returns:
            Trading signal dictionary
        """
        should_trade = False
        reason = ""
        
        # Decision logic
        confidence = processed_data.get('confidence', 0.0)
        recommendation = analysis_result.get('recommendation', 'CAUTION')
        
        if confidence >= 0.8 and recommendation in ['PROCEED', 'PROCEED_CAUTIOUSLY']:
            should_trade = True
            reason = "High confidence and favorable historical performance"
        elif confidence >= 0.7 and recommendation == 'PROCEED':
            should_trade = True
            reason = "Good confidence with strong historical performance"
        else:
            should_trade = False
            reason = f"Insufficient confidence ({confidence}) or poor historical performance ({recommendation})"
        
        # Calculate trade parameters
        entry_price = self._estimate_entry_price(symbol)  # Stub implementation
        target_price = entry_price * (1 + analysis_result.get('target_percentage', 0.05))
        stop_loss_price = entry_price * (1 - analysis_result.get('stop_loss_percentage', 0.02))
        
        # Calculate position size based on risk management
        position_size = self._calculate_position_size(
            entry_price, stop_loss_price, processed_data.get('order_value')
        )
        
        return self._create_signal(
            should_trade, reason, 
            symbol=symbol,
            entry_price=entry_price,
            target_price=target_price,
            stop_loss_price=stop_loss_price,
            position_size=position_size,
            confidence=confidence,
            strategy_data={
                'analysis_result': analysis_result,
                'processed_data': processed_data,
                'generated_at': datetime.now()
            }
        )
    
    def _estimate_entry_price(self, symbol: str) -> float:
        """
        Estimate entry price for the symbol.
        This is a stub - in production, get current market price from data provider.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Estimated entry price
        """
        # Stub implementation - return a dummy price
        # In production, integrate with market data provider
        self.logger.warning(f"Using dummy entry price for {symbol} - integrate with market data provider")
        return 100.0  # Dummy price
    
    def _calculate_position_size(self, entry_price: float, stop_loss_price: float, order_value: Optional[float]) -> int:
        """
        Calculate position size based on risk management rules.
        
        Args:
            entry_price: Entry price
            stop_loss_price: Stop loss price
            order_value: Order value from announcement
            
        Returns:
            Position size (number of shares)
        """
        # Risk per trade (from config)
        risk_per_trade = 0.02  # 2%
        max_position_value = 50000  # Rs. 50,000 max position
        
        # Calculate risk per share
        risk_per_share = entry_price - stop_loss_price
        
        if risk_per_share <= 0:
            return 0
        
        # Calculate maximum shares based on risk
        max_shares_by_risk = (max_position_value * risk_per_trade) / risk_per_share
        
        # Calculate maximum shares based on position value
        max_shares_by_value = max_position_value / entry_price
        
        # Take the minimum
        position_size = int(min(max_shares_by_risk, max_shares_by_value))
        
        return max(1, position_size)  # At least 1 share
    
    def _create_signal(self, should_trade: bool, reason: str, **kwargs) -> Dict:
        """
        Create a standardized trading signal.
        
        Args:
            should_trade: Whether to trade
            reason: Reason for decision
            **kwargs: Additional signal data
            
        Returns:
            Trading signal dictionary
        """
        signal = {
            'should_trade': should_trade,
            'reason': reason,
            'generated_at': datetime.now(),
            'symbol': kwargs.get('symbol', ''),
            'entry_price': kwargs.get('entry_price', 0.0),
            'target_price': kwargs.get('target_price', 0.0),
            'stop_loss_price': kwargs.get('stop_loss_price', 0.0),
            'position_size': kwargs.get('position_size', 0),
            'confidence': kwargs.get('confidence', 0.0),
            'strategy_data': kwargs.get('strategy_data', {})
        }
        
        return signal 