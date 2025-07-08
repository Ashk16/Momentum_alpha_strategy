#!/usr/bin/env python3
"""
Momentum Alpha - Main Application
Automated BSE Trading System

This is the main entry point for the Momentum Alpha trading system.
It orchestrates all modules and handles the main application loop.
"""

import asyncio
import argparse
import logging
import signal
import sys
from pathlib import Path
from typing import Optional

# Add src to path for imports
sys.path.append(str(Path(__file__).parent))

from utils.config_manager import ConfigManager
from utils.logger import setup_logging
from utils.database import DatabaseManager
from data_ingestion.bse_scraper import BSEScraper
from nlp_engine.announcement_processor import AnnouncementProcessor
from strategy_engine.trade_analyzer import TradeAnalyzer
from trade_executor.order_manager import OrderManager
from utils.risk_manager import RiskManager


class MomentumAlpha:
    """Main application class for the Momentum Alpha trading system."""
    
    def __init__(self, mode: str = "development"):
        self.mode = mode
        self.running = False
        self.config = None
        self.logger = None
        self.db_manager = None
        
        # Core modules
        self.bse_scraper = None
        self.nlp_processor = None
        self.trade_analyzer = None
        self.order_manager = None
        self.risk_manager = None
        
    async def initialize(self):
        """Initialize all components and connections."""
        try:
            # Load configuration
            self.config = ConfigManager()
            
            # Setup logging
            self.logger = setup_logging(
                level=self.config.get('logging.level', 'INFO'),
                mode=self.mode
            )
            
            self.logger.info(f"Initializing Momentum Alpha in {self.mode} mode")
            
            # Initialize database
            self.db_manager = DatabaseManager(self.config.get('database'))
            await self.db_manager.initialize()
            
            # Initialize core modules
            self.bse_scraper = BSEScraper(self.config.get('scraper'))
            self.nlp_processor = AnnouncementProcessor(self.config.get('nlp'))
            self.trade_analyzer = TradeAnalyzer(self.config.get('strategy'), self.db_manager)
            self.risk_manager = RiskManager(self.config.get('risk_management'))
            
            # Initialize order manager based on mode
            if self.mode in ['live', 'paper']:
                self.order_manager = OrderManager(
                    self.config.get('broker'),
                    paper_trading=(self.mode == 'paper')
                )
                await self.order_manager.initialize()
            
            self.logger.info("All modules initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize application: {e}")
            raise
    
    async def run(self):
        """Main application loop."""
        if not self.running:
            self.logger.error("Application not properly initialized")
            return
        
        self.logger.info("Starting main application loop")
        
        try:
            while self.running:
                # Main trading loop
                await self._process_announcements()
                
                # Sleep for configured interval
                await asyncio.sleep(self.config.get('scraper.poll_interval', 15))
                
        except Exception as e:
            self.logger.error(f"Error in main loop: {e}")
            raise
    
    async def _process_announcements(self):
        """Process new announcements and execute trades."""
        try:
            # Scrape for new announcements
            new_announcements = await self.bse_scraper.get_new_announcements()
            
            if not new_announcements:
                return
            
            self.logger.info(f"Found {len(new_announcements)} new announcements")
            
            for announcement in new_announcements:
                await self._process_single_announcement(announcement)
                
        except Exception as e:
            self.logger.error(f"Error processing announcements: {e}")
    
    async def _process_single_announcement(self, announcement: dict):
        """Process a single announcement through the entire pipeline."""
        try:
            # Step 1: NLP Processing
            processed_data = await self.nlp_processor.process_announcement(announcement)
            
            if not processed_data['is_tradeable']:
                self.logger.debug(f"Announcement not tradeable: {announcement['title']}")
                return
            
            # Step 2: Risk Management Check
            if not self.risk_manager.pre_trade_check(processed_data):
                self.logger.warning(f"Risk check failed for {processed_data['symbol']}")
                return
            
            # Step 3: Strategy Analysis
            trade_signal = await self.trade_analyzer.analyze_trade_opportunity(processed_data)
            
            if not trade_signal['should_trade']:
                self.logger.info(f"Strategy analysis rejected trade for {processed_data['symbol']}")
                return
            
            # Step 4: Execute Trade (if not in development mode)
            if self.mode != 'development' and self.order_manager:
                trade_result = await self.order_manager.execute_trade(trade_signal)
                self.logger.info(f"Trade executed: {trade_result}")
            else:
                self.logger.info(f"Would execute trade: {trade_signal} (development mode)")
                
        except Exception as e:
            self.logger.error(f"Error processing announcement: {e}")
    
    async def start(self):
        """Start the application."""
        self.running = True
        await self.initialize()
        await self.run()
    
    async def stop(self):
        """Stop the application gracefully."""
        self.logger.info("Stopping Momentum Alpha...")
        self.running = False
        
        # Cleanup resources
        if self.order_manager:
            await self.order_manager.cleanup()
        
        if self.db_manager:
            await self.db_manager.close()
        
        self.logger.info("Application stopped successfully")


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    print(f"\nReceived signal {signum}. Shutting down gracefully...")
    # Set a flag or use asyncio to stop the main loop
    asyncio.create_task(app.stop())


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Momentum Alpha - Automated BSE Trading System")
    parser.add_argument(
        '--mode',
        choices=['development', 'paper', 'live'],
        default='development',
        help='Trading mode (default: development)'
    )
    parser.add_argument(
        '--config',
        type=str,
        help='Path to custom config file'
    )
    
    args = parser.parse_args()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and run application
    global app
    app = MomentumAlpha(mode=args.mode)
    
    try:
        await app.start()
    except KeyboardInterrupt:
        print("\nReceived keyboard interrupt. Shutting down...")
    except Exception as e:
        print(f"Application error: {e}")
        sys.exit(1)
    finally:
        await app.stop()


if __name__ == "__main__":
    asyncio.run(main()) 