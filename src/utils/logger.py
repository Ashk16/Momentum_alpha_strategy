"""
Logging Utility
Provides centralized logging configuration for the application
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional

import colorlog


def setup_logging(
    level: str = "INFO",
    mode: str = "development",
    log_file: Optional[str] = None,
    max_file_size: str = "10MB",
    backup_count: int = 5
) -> logging.Logger:
    """
    Set up logging for the application.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        mode: Application mode (development, paper, live)
        log_file: Custom log file path
        max_file_size: Maximum size per log file
        backup_count: Number of backup log files to keep
        
    Returns:
        Configured logger instance
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Get project root and logs directory
    project_root = Path(__file__).parent.parent.parent
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Default log file based on mode
    if log_file is None:
        log_file = logs_dir / f"momentum_alpha_{mode}.log"
    else:
        log_file = Path(log_file)
    
    # Create formatter
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console formatter with colors (for development)
    console_formatter = colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s%(reset)s',
        datefmt='%H:%M:%S',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    
    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(numeric_level)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=_parse_file_size(max_file_size),
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    
    # Use colored output for development mode
    if mode == "development":
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.DEBUG)
    else:
        # Simpler format for production
        console_formatter_simple = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter_simple)
        console_handler.setLevel(logging.INFO)
    
    logger.addHandler(console_handler)
    
    # Add a separate error log file
    error_log_file = logs_dir / f"momentum_alpha_{mode}_errors.log"
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=_parse_file_size(max_file_size),
        backupCount=backup_count,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    logger.addHandler(error_handler)
    
    # Set specific logger levels for noisy libraries
    _configure_third_party_loggers()
    
    # Log initial setup message
    logger.info(f"Logging initialized - Level: {level}, Mode: {mode}")
    logger.info(f"Log file: {log_file}")
    logger.info(f"Error log file: {error_log_file}")
    
    return logger


def _parse_file_size(size_str: str) -> int:
    """
    Parse file size string to bytes.
    
    Args:
        size_str: Size string like "10MB", "1GB", etc.
        
    Returns:
        Size in bytes
    """
    size_str = size_str.upper()
    
    if size_str.endswith('KB'):
        return int(size_str[:-2]) * 1024
    elif size_str.endswith('MB'):
        return int(size_str[:-2]) * 1024 * 1024
    elif size_str.endswith('GB'):
        return int(size_str[:-2]) * 1024 * 1024 * 1024
    else:
        # Assume bytes
        return int(size_str)


def _configure_third_party_loggers():
    """Configure logging levels for third-party libraries to reduce noise."""
    # Reduce verbosity of common libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    
    # Database libraries
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
    logging.getLogger('alembic').setLevel(logging.WARNING)
    
    # Trading API libraries
    logging.getLogger('kiteconnect').setLevel(logging.INFO)
    logging.getLogger('fyers_api').setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class TradeLogger:
    """Specialized logger for trade-related activities."""
    
    def __init__(self, mode: str = "development"):
        self.mode = mode
        self.logger = get_logger("trades")
        
        # Create separate trade log file
        project_root = Path(__file__).parent.parent.parent
        logs_dir = project_root / "logs"
        trade_log_file = logs_dir / f"trades_{mode}.log"
        
        # Trade-specific formatter
        trade_formatter = logging.Formatter(
            '%(asctime)s - TRADE - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Trade file handler
        trade_handler = logging.handlers.RotatingFileHandler(
            trade_log_file,
            maxBytes=50 * 1024 * 1024,  # 50MB
            backupCount=10,
            encoding='utf-8'
        )
        trade_handler.setFormatter(trade_formatter)
        trade_handler.setLevel(logging.INFO)
        
        self.logger.addHandler(trade_handler)
    
    def trade_signal(self, symbol: str, signal_data: dict):
        """Log trade signal generation."""
        self.logger.info(f"SIGNAL - {symbol}: {signal_data}")
    
    def trade_execution(self, symbol: str, order_data: dict):
        """Log trade execution."""
        self.logger.info(f"EXECUTION - {symbol}: {order_data}")
    
    def trade_result(self, symbol: str, result_data: dict):
        """Log trade results."""
        self.logger.info(f"RESULT - {symbol}: {result_data}")
    
    def risk_check(self, symbol: str, risk_data: dict, passed: bool):
        """Log risk check results."""
        status = "PASSED" if passed else "FAILED"
        self.logger.info(f"RISK_CHECK - {symbol} - {status}: {risk_data}")


# Convenience function for trade logging
def get_trade_logger(mode: str = "development") -> TradeLogger:
    """Get a trade logger instance."""
    return TradeLogger(mode) 