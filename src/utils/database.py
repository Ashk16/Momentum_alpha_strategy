"""
Database Manager
Handles database connections and operations
"""

import asyncio
from typing import Dict, List, Optional, Any

try:
    import asyncpg
    ASYNCPG_AVAILABLE = True
except ImportError:
    ASYNCPG_AVAILABLE = False

import sqlite3
import aiosqlite
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, DateTime, Float, Boolean, Text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from .logger import get_logger


class DatabaseManager:
    """Manages database connections and operations."""
    
    def __init__(self, config: Dict):
        """
        Initialize database manager.
        
        Args:
            config: Database configuration dictionary
        """
        self.config = config
        self.logger = get_logger(__name__)
        
        self.db_type = config.get('type', 'sqlite')
        self.engine = None
        self.async_session = None
        self.metadata = MetaData()
        
        # Define tables
        self._define_tables()
        
    def _define_tables(self):
        """Define database tables."""
        # Announcements table
        self.announcements_table = Table(
            'announcements',
            self.metadata,
            Column('id', Integer, primary_key=True),
            Column('hash', String(32), unique=True, nullable=False),
            Column('timestamp', DateTime, default=datetime.utcnow),
            Column('scrape_time', DateTime, default=datetime.utcnow),
            Column('date', String(20)),
            Column('time', String(20)),
            Column('company_name', String(200)),
            Column('title', Text),
            Column('category', String(100)),
            Column('pdf_url', String(500)),
            Column('processed', Boolean, default=False),
            Column('is_tradeable', Boolean, default=False),
            Column('extracted_data', Text),  # JSON string
        )
        
        # Trades table
        self.trades_table = Table(
            'trades',
            self.metadata,
            Column('id', Integer, primary_key=True),
            Column('announcement_hash', String(32)),
            Column('symbol', String(20)),
            Column('entry_time', DateTime),
            Column('exit_time', DateTime),
            Column('entry_price', Float),
            Column('exit_price', Float),
            Column('quantity', Integer),
            Column('target_price', Float),
            Column('stop_loss', Float),
            Column('profit_loss', Float),
            Column('status', String(20)),  # OPEN, CLOSED, CANCELLED
            Column('order_id', String(50)),
            Column('strategy_data', Text),  # JSON string
        )
        
        # Performance metrics table
        self.performance_table = Table(
            'performance_metrics',
            self.metadata,
            Column('id', Integer, primary_key=True),
            Column('date', DateTime, default=datetime.utcnow),
            Column('total_trades', Integer, default=0),
            Column('winning_trades', Integer, default=0),
            Column('losing_trades', Integer, default=0),
            Column('total_pnl', Float, default=0.0),
            Column('win_rate', Float, default=0.0),
            Column('avg_profit', Float, default=0.0),
            Column('avg_loss', Float, default=0.0),
            Column('max_drawdown', Float, default=0.0),
            Column('sharpe_ratio', Float, default=0.0),
        )
    
    async def initialize(self):
        """Initialize database connection."""
        try:
            if self.db_type == 'postgresql':
                if not ASYNCPG_AVAILABLE:
                    raise ImportError("asyncpg not available. Install with: pip install asyncpg")
                
                host = self.config.get('host', 'localhost')
                port = self.config.get('port', 5432)
                database = self.config.get('name', 'momentum_alpha')
                username = self.config.get('username')
                password = self.config.get('password')
                
                if not username or not password:
                    raise ValueError("PostgreSQL username and password required")
                
                db_url = f"postgresql+asyncpg://{username}:{password}@{host}:{port}/{database}"
                self.engine = create_async_engine(db_url, echo=False)
                
            else:  # SQLite
                db_path = self.config.get('sqlite_path', 'data/momentum_alpha.db')
                db_url = f"sqlite+aiosqlite:///{db_path}"
                self.engine = create_async_engine(db_url, echo=False)
            
            # Create async session factory
            self.async_session = sessionmaker(
                self.engine, class_=AsyncSession, expire_on_commit=False
            )
            
            self.logger.info(f"Database connection initialized: {self.db_type}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def create_tables(self):
        """Create database tables."""
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(self.metadata.create_all)
            
            self.logger.info("Database tables created successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to create tables: {e}")
            raise
    
    async def close(self):
        """Close database connection."""
        if self.engine:
            await self.engine.dispose()
            self.logger.info("Database connection closed")
    
    async def save_announcement(self, announcement: Dict) -> int:
        """
        Save announcement to database.
        
        Args:
            announcement: Announcement dictionary
            
        Returns:
            Announcement ID
        """
        try:
            async with self.async_session() as session:
                # Check if announcement already exists
                existing = await session.execute(
                    self.announcements_table.select().where(
                        self.announcements_table.c.hash == announcement.get('hash')
                    )
                )
                
                if existing.fetchone():
                    self.logger.debug(f"Announcement already exists: {announcement.get('hash')}")
                    return None
                
                # Insert new announcement
                result = await session.execute(
                    self.announcements_table.insert().values(**announcement)
                )
                
                await session.commit()
                
                announcement_id = result.inserted_primary_key[0]
                self.logger.debug(f"Saved announcement ID: {announcement_id}")
                
                return announcement_id
                
        except Exception as e:
            self.logger.error(f"Failed to save announcement: {e}")
            raise
    
    async def save_trade(self, trade_data: Dict) -> int:
        """
        Save trade to database.
        
        Args:
            trade_data: Trade dictionary
            
        Returns:
            Trade ID
        """
        try:
            async with self.async_session() as session:
                result = await session.execute(
                    self.trades_table.insert().values(**trade_data)
                )
                
                await session.commit()
                
                trade_id = result.inserted_primary_key[0]
                self.logger.debug(f"Saved trade ID: {trade_id}")
                
                return trade_id
                
        except Exception as e:
            self.logger.error(f"Failed to save trade: {e}")
            raise
    
    async def update_trade(self, trade_id: int, updates: Dict):
        """
        Update trade in database.
        
        Args:
            trade_id: Trade ID
            updates: Dictionary of fields to update
        """
        try:
            async with self.async_session() as session:
                await session.execute(
                    self.trades_table.update()
                    .where(self.trades_table.c.id == trade_id)
                    .values(**updates)
                )
                
                await session.commit()
                
                self.logger.debug(f"Updated trade ID: {trade_id}")
                
        except Exception as e:
            self.logger.error(f"Failed to update trade: {e}")
            raise
    
    async def get_historical_trades(self, symbol: str = None, days: int = 30) -> List[Dict]:
        """
        Get historical trades.
        
        Args:
            symbol: Filter by symbol (optional)
            days: Number of days to look back
            
        Returns:
            List of trade dictionaries
        """
        try:
            async with self.async_session() as session:
                query = self.trades_table.select()
                
                if symbol:
                    query = query.where(self.trades_table.c.symbol == symbol)
                
                # Add date filter
                from datetime import datetime, timedelta
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                query = query.where(self.trades_table.c.entry_time >= cutoff_date)
                
                result = await session.execute(query)
                trades = [dict(row) for row in result.fetchall()]
                
                return trades
                
        except Exception as e:
            self.logger.error(f"Failed to get historical trades: {e}")
            return []
    
    async def get_performance_metrics(self) -> Dict:
        """
        Get performance metrics.
        
        Returns:
            Performance metrics dictionary
        """
        try:
            async with self.async_session() as session:
                # Get latest performance record
                query = self.performance_table.select().order_by(
                    self.performance_table.c.date.desc()
                ).limit(1)
                
                result = await session.execute(query)
                row = result.fetchone()
                
                if row:
                    return dict(row)
                else:
                    return {
                        'total_trades': 0,
                        'winning_trades': 0,
                        'losing_trades': 0,
                        'total_pnl': 0.0,
                        'win_rate': 0.0,
                        'avg_profit': 0.0,
                        'avg_loss': 0.0,
                        'max_drawdown': 0.0,
                        'sharpe_ratio': 0.0,
                    }
                    
        except Exception as e:
            self.logger.error(f"Failed to get performance metrics: {e}")
            return {}
    
    async def health_check(self) -> bool:
        """
        Check database health.
        
        Returns:
            True if database is healthy, False otherwise
        """
        try:
            async with self.async_session() as session:
                await session.execute("SELECT 1")
                return True
                
        except Exception as e:
            self.logger.error(f"Database health check failed: {e}")
            return False 