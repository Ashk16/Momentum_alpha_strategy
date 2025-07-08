# 🏗️ Project Structure - Momentum Alpha

## Overview
Momentum Alpha is an automated BSE trading system designed with a modular architecture. This document provides a comprehensive guide to the project structure, explaining the purpose of each module and how they interact.

## 📁 Directory Structure

```
momentum_alpha/
├── 📋 Documentation & Configuration
│   ├── README.md                              # Main project documentation
│   ├── Momentum_Alpha_Project_Document.md     # Detailed project specification
│   ├── PROJECT_STRUCTURE.md                   # This file - architecture guide
│   ├── requirements.txt                       # Python dependencies
│   ├── .gitignore                            # Git ignore rules
│   └── config/
│       └── config.template.yaml              # Configuration template
│
├── 🔧 Core Application
│   └── src/
│       ├── main.py                           # Application entry point & orchestrator
│       ├── __init__.py                       # Package initialization
│       │
│       ├── 📡 data_ingestion/                # MODULE 1: Data Collection
│       │   ├── __init__.py
│       │   └── bse_scraper.py                # BSE website scraper
│       │
│       ├── 🧠 nlp_engine/                    # MODULE 2: Text Analysis
│       │   ├── __init__.py
│       │   └── announcement_processor.py     # NLP processing & filtering
│       │
│       ├── 📊 strategy_engine/               # MODULE 3: Trading Logic
│       │   ├── __init__.py
│       │   ├── trade_analyzer.py             # Historical analysis & signals
│       │   └── backtest.py                   # Backtesting engine (future)
│       │
│       ├── 💰 trade_executor/                # MODULE 4: Order Management
│       │   ├── __init__.py
│       │   ├── order_manager.py              # Trade execution
│       │   └── broker_interface.py           # Broker API abstraction (future)
│       │
│       └── 🔧 utils/                         # Shared Utilities
│           ├── __init__.py
│           ├── config_manager.py             # Configuration management
│           ├── logger.py                     # Logging system
│           ├── database.py                   # Database operations
│           └── risk_manager.py               # Risk management
│
├── 🗄️ Data & Storage
│   ├── data/                                 # Data files (CSV, JSON, etc.)
│   └── logs/                                 # Application logs
│
├── 🧪 Development & Testing
│   ├── tests/
│   │   ├── unit/                            # Unit tests
│   │   └── integration/                     # Integration tests
│   └── scripts/
│       └── setup_database.py               # Database initialization
│
└── 📚 docs/                                  # Additional documentation
```

---

## 🏛️ Architecture Overview

### Core Philosophy
- **Modular Design**: Each module has a single responsibility
- **Async-First**: Built for high-performance concurrent operations
- **Safety-First**: Multiple layers of risk management and validation
- **Production-Ready**: Comprehensive logging, error handling, and monitoring

### Data Flow
```
BSE Website → Scraper → NLP Engine → Strategy Engine → Risk Manager → Trade Executor → Broker API
     ↓            ↓           ↓             ↓              ↓             ↓
  Database ← Database ← Database ← Database ← Database ← Database
```

---

## 📡 Module 1: Data Ingestion (`src/data_ingestion/`)

### Purpose
Ethical web scraping of BSE corporate announcements with real-time monitoring.

### Key Components
- **`bse_scraper.py`**: Main scraper class with retry logic and rate limiting

### Responsibilities
- ✅ Monitor BSE announcements page every 15 seconds
- ✅ Detect new announcements using content diff
- ✅ Extract announcement metadata (title, company, date, PDF links)
- ✅ Respect robots.txt and implement polite delays
- ✅ Handle network failures with exponential backoff
- ✅ Deduplicate announcements using hash signatures

### Key Features
- Async HTTP client with connection pooling
- Configurable polling intervals and timeouts
- Comprehensive error handling and logging
- BeautifulSoup HTML parsing
- PDF link extraction

---

## 🧠 Module 2: NLP Engine (`src/nlp_engine/`)

### Purpose
Process and analyze announcement text to identify tradeable "Award of Order" events.

### Key Components
- **`announcement_processor.py`**: NLP analysis engine with spaCy integration

### Responsibilities
- ✅ Filter announcements using keyword matching
- ✅ Extract order values (Rs. X Crore/Lakh format)
- ✅ Identify company symbols from names
- ✅ Calculate confidence scores for trading decisions
- ✅ Perform advanced NLP analysis (entities, patterns)
- ✅ Validate minimum order value thresholds

### Key Features
- SpaCy integration for advanced NLP
- Regular expression pattern matching
- Confidence scoring algorithm
- Multi-level keyword filtering (primary/secondary)
- Currency amount extraction and conversion
- False positive detection

---

## 📊 Module 3: Strategy Engine (`src/strategy_engine/`)

### Purpose
Analyze historical performance and generate trading signals based on data-driven strategies.

### Key Components
- **`trade_analyzer.py`**: Historical analysis and signal generation
- **`backtest.py`**: Backtesting engine (planned for future implementation)

### Responsibilities
- ✅ Query historical trade performance for similar announcements
- ✅ Calculate win rates, average profits/losses
- ✅ Determine optimal entry/exit prices
- ✅ Set dynamic stop-loss and target levels
- ✅ Calculate position sizes based on risk parameters
- ✅ Generate final trading recommendations

### Key Features
- Historical performance analysis
- Dynamic target and stop-loss calculation
- Risk-adjusted position sizing
- Confidence-based decision making
- Default strategy for new symbols
- Performance metrics tracking

---

## 💰 Module 4: Trade Executor (`src/trade_executor/`)

### Purpose
Execute trades through broker APIs with comprehensive order management.

### Key Components
- **`order_manager.py`**: Order execution and management
- **`broker_interface.py`**: Broker API abstraction (planned)

### Responsibilities
- ✅ Execute trades via multiple broker APIs (Zerodha, Fyers)
- ✅ Support paper trading mode for testing
- ✅ Place bracket orders with automatic targets and stop-losses
- ✅ Monitor order status and position management
- ✅ Handle partial fills and order modifications
- ✅ Maintain trade history and performance tracking

### Key Features
- Multi-broker support (Zerodha Kite, Fyers API)
- Paper trading simulation
- Bracket order placement
- Real-time order status monitoring
- Position tracking and management
- Comprehensive error handling

---

## 🔧 Utilities (`src/utils/`)

### Purpose
Shared utilities and services used across all modules.

### Key Components

#### `config_manager.py`
- **Purpose**: Centralized configuration management
- **Features**: YAML config loading, environment variable override, dot notation access

#### `logger.py`
- **Purpose**: Comprehensive logging system
- **Features**: Colored console output, file rotation, separate error logs, trade-specific logging

#### `database.py`
- **Purpose**: Database operations and ORM
- **Features**: PostgreSQL/SQLite support, async operations, table management

#### `risk_manager.py`
- **Purpose**: Risk management and pre-trade validation
- **Features**: Position sizing, daily limits, market condition checks, emergency stops

---

## 🗄️ Data Management

### Database Schema
- **`announcements`**: Store all scraped announcements
- **`trades`**: Track all executed trades and their outcomes
- **`performance_metrics`**: Daily/weekly performance statistics

### Configuration
- **`config.template.yaml`**: Template with all configuration options
- **Environment Variables**: Override sensitive values (API keys, passwords)

### Logging Strategy
- **Application Logs**: General system operations
- **Trade Logs**: Dedicated trade-specific logging
- **Error Logs**: Separate error tracking
- **File Rotation**: Automatic log file management

---

## 🔄 Operational Flow

### 1. Startup Sequence
```python
main.py → ConfigManager → DatabaseManager → All Modules → Main Loop
```

### 2. Processing Pipeline
```python
BSE Scraper → New Announcement → NLP Processing → Risk Check → Strategy Analysis → Trade Execution → Database Update
```

### 3. Trading Modes
- **Development**: Full logging, no actual trades
- **Paper Trading**: Simulated trades with virtual money
- **Live Trading**: Real trades with actual money

---

## 🚀 Development Workflow

### Initial Setup
1. Copy `config/config.template.yaml` to `config/config.yaml`
2. Configure API keys and database settings
3. Run `python scripts/setup_database.py`
4. Start with `python src/main.py --mode development`

### Testing Strategy
1. **Unit Tests**: Test individual module functions
2. **Integration Tests**: Test module interactions
3. **Paper Trading**: Test full system with simulated money
4. **Live Trading**: Deploy with real money (after thorough testing)

### Safety Protocols
- ⚠️ Always start with paper trading
- ⚠️ Set conservative position limits
- ⚠️ Monitor logs regularly
- ⚠️ Have emergency stop procedures

---

## 🔮 Future Enhancements

### Planned Features
- [ ] **Multi-Exchange Support**: NSE integration
- [ ] **Advanced ML Models**: Deep learning for announcement classification
- [ ] **Real-Time Dashboard**: Web-based monitoring interface
- [ ] **Mobile Alerts**: Push notifications for trades
- [ ] **Advanced Backtesting**: Historical strategy validation
- [ ] **Portfolio Management**: Multi-symbol position tracking

### Scalability Considerations
- **Microservices**: Split modules into separate services
- **Message Queues**: Async communication between modules
- **Load Balancing**: Multiple scraper instances
- **Caching**: Redis for performance optimization
- **Monitoring**: Prometheus/Grafana integration

---

## 📞 Support & Maintenance

### Key Metrics to Monitor
- **System Uptime**: Target 99%+ availability
- **Scraping Success Rate**: Monitor BSE connectivity
- **NLP Accuracy**: Track false positive rates
- **Trade Execution Speed**: Latency monitoring
- **Risk Metrics**: Daily P&L, position sizes

### Troubleshooting Guide
- **Database Issues**: Check connection strings and permissions
- **API Failures**: Verify broker API credentials and limits
- **Scraping Problems**: Check robots.txt compliance and rate limits
- **Performance Issues**: Monitor memory usage and async operations

---

## 📋 File Naming Conventions

### Python Files
- **Classes**: PascalCase (e.g., `BSEScraper`, `OrderManager`)
- **Functions**: snake_case (e.g., `process_announcement`, `execute_trade`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_RETRIES`, `API_TIMEOUT`)

### Configuration
- **YAML Keys**: snake_case (e.g., `max_position_size`, `poll_interval`)
- **Environment Variables**: UPPER_SNAKE_CASE (e.g., `POSTGRES_HOST`, `BROKER_API_KEY`)

---

*This document should be updated whenever significant architectural changes are made to the system.* 