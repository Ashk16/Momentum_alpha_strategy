#!/usr/bin/env python3
"""
Database Setup Script
Initialize database schema for Momentum Alpha
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from utils.config_manager import ConfigManager
from utils.logger import setup_logging
from utils.database import DatabaseManager


async def setup_database():
    """Set up the database schema."""
    print("🚀 Setting up Momentum Alpha database...")
    
    try:
        # Load configuration
        config = ConfigManager()
        
        # Setup logging
        logger = setup_logging(level="INFO", mode="setup")
        
        # Initialize database manager
        db_config = config.get_section('database')
        db_manager = DatabaseManager(db_config)
        
        # Create database and tables
        await db_manager.initialize()
        await db_manager.create_tables()
        
        print("✅ Database setup completed successfully!")
        print(f"📊 Database: {db_config.get('name', 'momentum_alpha')}")
        print(f"🏠 Host: {db_config.get('host', 'localhost')}")
        
        # Close database connection
        await db_manager.close()
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        sys.exit(1)


def main():
    """Main function."""
    print("=" * 50)
    print("   Momentum Alpha - Database Setup")
    print("=" * 50)
    
    asyncio.run(setup_database())


if __name__ == "__main__":
    main() 