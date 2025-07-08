"""
Order Manager - Trade Executor
Handles order execution and broker API integration
"""

from typing import Dict, List, Optional
from datetime import datetime
import asyncio

from ..utils.logger import get_logger


class OrderManager:
    """Manages order execution and broker API integration."""
    
    def __init__(self, config: Dict, paper_trading: bool = True):
        """
        Initialize order manager.
        
        Args:
            config: Broker configuration dictionary
            paper_trading: Whether to run in paper trading mode
        """
        self.config = config
        self.paper_trading = paper_trading
        self.logger = get_logger(__name__)
        
        self.broker_name = config.get('name', 'zerodha')
        self.api_key = config.get('api_key')
        self.api_secret = config.get('api_secret')
        self.access_token = config.get('access_token')
        
        # Paper trading settings
        if paper_trading:
            self.paper_balance = config.get('paper_trading', {}).get('initial_balance', 100000)
            self.paper_positions = {}
            self.paper_orders = []
        
        self.broker_client = None
        
        self.logger.info(f"Order Manager initialized - Paper Trading: {paper_trading}")
    
    async def initialize(self):
        """Initialize broker connection."""
        try:
            if self.paper_trading:
                self.logger.info("Running in paper trading mode")
                return
            
            # Initialize broker client based on broker type
            if self.broker_name.lower() == 'zerodha':
                await self._initialize_zerodha()
            elif self.broker_name.lower() == 'fyers':
                await self._initialize_fyers()
            else:
                raise ValueError(f"Unsupported broker: {self.broker_name}")
            
            self.logger.info(f"Broker connection initialized: {self.broker_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize broker connection: {e}")
            raise
    
    async def _initialize_zerodha(self):
        """Initialize Zerodha Kite Connect."""
        try:
            # Import here to avoid dependency issues
            from kiteconnect import KiteConnect
            
            if not self.api_key or not self.access_token:
                raise ValueError("Zerodha API key and access token required")
            
            self.broker_client = KiteConnect(api_key=self.api_key)
            self.broker_client.set_access_token(self.access_token)
            
            # Test connection
            profile = self.broker_client.profile()
            self.logger.info(f"Connected to Zerodha - User: {profile.get('user_name', 'Unknown')}")
            
        except ImportError:
            raise ImportError("kiteconnect package not found. Install with: pip install kiteconnect")
        except Exception as e:
            raise Exception(f"Failed to initialize Zerodha: {e}")
    
    async def _initialize_fyers(self):
        """Initialize Fyers API."""
        try:
            # Import here to avoid dependency issues
            from fyers_api import fyersModel
            
            if not self.api_key or not self.access_token:
                raise ValueError("Fyers API key and access token required")
            
            self.broker_client = fyersModel.FyersModel(
                client_id=self.api_key,
                token=self.access_token,
                log_path=""
            )
            
            # Test connection
            response = self.broker_client.get_profile()
            if response['s'] == 'ok':
                self.logger.info(f"Connected to Fyers - User: {response['data'].get('name', 'Unknown')}")
            else:
                raise Exception(f"Fyers connection failed: {response}")
                
        except ImportError:
            raise ImportError("fyers-apiv2 package not found. Install with: pip install fyers-apiv2")
        except Exception as e:
            raise Exception(f"Failed to initialize Fyers: {e}")
    
    async def execute_trade(self, trade_signal: Dict) -> Dict:
        """
        Execute a trade based on the trading signal.
        
        Args:
            trade_signal: Trading signal dictionary
            
        Returns:
            Trade execution result
        """
        try:
            if not trade_signal.get('should_trade', False):
                return {'status': 'SKIPPED', 'reason': 'No trade signal'}
            
            symbol = trade_signal.get('symbol', '')
            entry_price = trade_signal.get('entry_price', 0.0)
            target_price = trade_signal.get('target_price', 0.0)
            stop_loss_price = trade_signal.get('stop_loss_price', 0.0)
            position_size = trade_signal.get('position_size', 0)
            
            if not symbol or position_size <= 0:
                return {'status': 'FAILED', 'reason': 'Invalid trade parameters'}
            
            # Execute based on mode
            if self.paper_trading:
                result = await self._execute_paper_trade(trade_signal)
            else:
                result = await self._execute_live_trade(trade_signal)
            
            self.logger.info(f"Trade executed for {symbol}: {result['status']}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error executing trade: {e}")
            return {'status': 'FAILED', 'reason': f'Execution error: {e}'}
    
    async def _execute_paper_trade(self, trade_signal: Dict) -> Dict:
        """Execute trade in paper trading mode."""
        symbol = trade_signal.get('symbol', '')
        entry_price = trade_signal.get('entry_price', 0.0)
        position_size = trade_signal.get('position_size', 0)
        
        # Calculate trade value
        trade_value = entry_price * position_size
        
        # Check if we have enough balance
        if trade_value > self.paper_balance:
            return {'status': 'FAILED', 'reason': 'Insufficient paper trading balance'}
        
        # Execute paper trade
        order_id = f"PAPER_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Deduct from balance
        self.paper_balance -= trade_value
        
        # Add to positions
        self.paper_positions[symbol] = {
            'symbol': symbol,
            'quantity': position_size,
            'entry_price': entry_price,
            'entry_time': datetime.now(),
            'target_price': trade_signal.get('target_price', 0.0),
            'stop_loss_price': trade_signal.get('stop_loss_price', 0.0),
            'order_id': order_id
        }
        
        # Record order
        self.paper_orders.append({
            'order_id': order_id,
            'symbol': symbol,
            'quantity': position_size,
            'price': entry_price,
            'order_type': 'BUY',
            'status': 'COMPLETED',
            'timestamp': datetime.now()
        })
        
        return {
            'status': 'COMPLETED',
            'order_id': order_id,
            'symbol': symbol,
            'quantity': position_size,
            'price': entry_price,
            'trade_value': trade_value,
            'remaining_balance': self.paper_balance
        }
    
    async def _execute_live_trade(self, trade_signal: Dict) -> Dict:
        """Execute trade with live broker API."""
        if not self.broker_client:
            return {'status': 'FAILED', 'reason': 'Broker client not initialized'}
        
        symbol = trade_signal.get('symbol', '')
        position_size = trade_signal.get('position_size', 0)
        target_price = trade_signal.get('target_price', 0.0)
        stop_loss_price = trade_signal.get('stop_loss_price', 0.0)
        
        try:
            # Place bracket order (or cover order)
            if self.broker_name.lower() == 'zerodha':
                result = await self._place_zerodha_order(trade_signal)
            elif self.broker_name.lower() == 'fyers':
                result = await self._place_fyers_order(trade_signal)
            else:
                return {'status': 'FAILED', 'reason': f'Unsupported broker: {self.broker_name}'}
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error placing live order: {e}")
            return {'status': 'FAILED', 'reason': f'Order placement error: {e}'}
    
    async def _place_zerodha_order(self, trade_signal: Dict) -> Dict:
        """Place order using Zerodha Kite Connect."""
        symbol = trade_signal.get('symbol', '')
        position_size = trade_signal.get('position_size', 0)
        target_price = trade_signal.get('target_price', 0.0)
        stop_loss_price = trade_signal.get('stop_loss_price', 0.0)
        
        # Zerodha bracket order parameters
        order_params = {
            'exchange': 'BSE',
            'tradingsymbol': symbol,
            'transaction_type': 'BUY',
            'quantity': position_size,
            'order_type': 'MARKET',
            'product': 'MIS',  # Intraday
            'validity': 'DAY',
            'squareoff': target_price,  # Target
            'stoploss': stop_loss_price,  # Stop loss
            'variety': 'bo'  # Bracket order
        }
        
        try:
            response = self.broker_client.place_order(**order_params)
            order_id = response.get('order_id')
            
            return {
                'status': 'PLACED',
                'order_id': order_id,
                'symbol': symbol,
                'quantity': position_size,
                'broker_response': response
            }
            
        except Exception as e:
            return {'status': 'FAILED', 'reason': f'Zerodha order failed: {e}'}
    
    async def _place_fyers_order(self, trade_signal: Dict) -> Dict:
        """Place order using Fyers API."""
        symbol = trade_signal.get('symbol', '')
        position_size = trade_signal.get('position_size', 0)
        
        # Fyers order parameters
        order_params = {
            'symbol': f'BSE:{symbol}-EQ',
            'qty': position_size,
            'type': 2,  # Market order
            'side': 1,  # Buy
            'productType': 'INTRADAY',
            'limitPrice': 0,
            'stopPrice': 0,
            'validity': 'DAY',
            'disclosedQty': 0,
            'offlineOrder': False,
            'stopLoss': trade_signal.get('stop_loss_price', 0.0),
            'takeProfit': trade_signal.get('target_price', 0.0)
        }
        
        try:
            response = self.broker_client.place_order(order_params)
            
            if response['s'] == 'ok':
                order_id = response['data']['id']
                return {
                    'status': 'PLACED',
                    'order_id': order_id,
                    'symbol': symbol,
                    'quantity': position_size,
                    'broker_response': response
                }
            else:
                return {'status': 'FAILED', 'reason': f'Fyers order failed: {response}'}
                
        except Exception as e:
            return {'status': 'FAILED', 'reason': f'Fyers order failed: {e}'}
    
    async def get_positions(self) -> List[Dict]:
        """Get current positions."""
        if self.paper_trading:
            return list(self.paper_positions.values())
        
        # Get live positions from broker
        if not self.broker_client:
            return []
        
        try:
            if self.broker_name.lower() == 'zerodha':
                positions = self.broker_client.positions()
                return positions.get('day', [])
            elif self.broker_name.lower() == 'fyers':
                response = self.broker_client.positions()
                if response['s'] == 'ok':
                    return response.get('data', {}).get('overall', [])
            
            return []
            
        except Exception as e:
            self.logger.error(f"Error getting positions: {e}")
            return []
    
    async def get_order_status(self, order_id: str) -> Dict:
        """Get order status."""
        if self.paper_trading:
            # Find order in paper orders
            for order in self.paper_orders:
                if order['order_id'] == order_id:
                    return order
            return {}
        
        # Get live order status from broker
        if not self.broker_client:
            return {}
        
        try:
            if self.broker_name.lower() == 'zerodha':
                orders = self.broker_client.orders()
                for order in orders:
                    if order.get('order_id') == order_id:
                        return order
            elif self.broker_name.lower() == 'fyers':
                response = self.broker_client.orderbook()
                if response['s'] == 'ok':
                    for order in response.get('data', {}).get('orderBook', []):
                        if order.get('id') == order_id:
                            return order
            
            return {}
            
        except Exception as e:
            self.logger.error(f"Error getting order status: {e}")
            return {}
    
    async def cleanup(self):
        """Clean up resources."""
        if self.paper_trading:
            self.logger.info(f"Paper trading session ended - Final balance: {self.paper_balance}")
        
        if self.broker_client:
            # Close broker connection if needed
            self.broker_client = None
        
        self.logger.info("Order Manager cleanup completed") 