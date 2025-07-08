# Momentum Alpha - Automated BSE Trading System

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An automated trading system designed to capitalize on short-term market inefficiencies following "Award of Order" announcements on the Bombay Stock Exchange (BSE).

## 🚀 Overview

Momentum Alpha is a sophisticated algorithmic trading system that:
- Monitors BSE corporate announcements in real-time
- Uses NLP to identify "Award of Order" events
- Calculates optimal entry/exit points based on historical analysis
- Executes trades automatically via brokerage APIs
- Manages risk through dynamic stop-losses and position sizing

## 📋 Prerequisites

- Python 3.8 or higher
- Active brokerage account with API access (Zerodha/Fyers/etc.)
- VPS or cloud server for 24/7 operation
- PostgreSQL (recommended) or SQLite for data storage

## 🛠️ Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd Award_of_order
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Download NLP models:**
```bash
python -m spacy download en_core_web_sm
```

5. **Set up configuration:**
```bash
cp config/config.template.yaml config/config.yaml
# Edit config.yaml with your API keys and settings
```

6. **Initialize database:**
```bash
python scripts/setup_database.py
```

## 🏗️ Project Structure

```
momentum_alpha/
├── src/
│   ├── data_ingestion/          # Module 1: Web Scraper
│   ├── nlp_engine/              # Module 2: NLP & Filtering
│   ├── strategy_engine/         # Module 3: Historical Analysis
│   ├── trade_executor/          # Module 4: Trade Execution
│   ├── utils/                   # Shared utilities
│   └── main.py                  # Main application entry point
├── config/                      # Configuration files
├── data/                        # Data storage
├── tests/                       # Unit and integration tests
├── scripts/                     # Setup and utility scripts
├── docs/                        # Documentation
├── logs/                        # Application logs
└── requirements.txt             # Python dependencies
```

## ⚙️ Configuration

Edit `config/config.yaml` to set up:

- **Broker API credentials**
- **Database connection settings**
- **Trading parameters** (position size, risk limits)
- **Scraping intervals and timeouts**
- **NLP model settings**

## 🚦 Usage

### Development Mode
```bash
python src/main.py --mode development
```

### Paper Trading
```bash
python src/main.py --mode paper
```

### Live Trading (Use with caution!)
```bash
python src/main.py --mode live
```

### Backtesting
```bash
python src/strategy_engine/backtest.py --start-date 2023-01-01 --end-date 2023-12-31
```

## 🧪 Testing

Run the test suite:
```bash
# All tests
pytest tests/

# Specific module
pytest tests/test_nlp_engine.py

# With coverage
pytest --cov=src tests/
```

## 📊 Monitoring

The system provides real-time monitoring through:
- **Logs**: Check `logs/` directory for detailed operation logs
- **Database**: Query trade history and performance metrics
- **Alerts**: Email/SMS notifications for critical events

## 🔒 Risk Management

**IMPORTANT SAFETY MEASURES:**

1. **Start with paper trading** - Never begin with live money
2. **Small position sizes** - Risk only 1-2% per trade initially
3. **Monitor system health** - Check logs and alerts regularly
4. **Have kill switches** - Know how to stop the system quickly
5. **Regular backtesting** - Validate strategy performance continuously

## 📈 Performance Metrics

Track these key metrics:
- **ROI**: Return on Investment
- **Sharpe Ratio**: Risk-adjusted returns (target: >1.5)
- **Max Drawdown**: Largest peak-to-trough decline
- **Win Rate**: Percentage of profitable trades
- **Average Trade Duration**: Time from entry to exit

## 🚨 Disclaimer

**This software is for educational purposes only. Trading involves substantial risk of loss and is not suitable for all investors. Past performance is not indicative of future results. Use at your own risk.**

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 Support

For questions and support:
- Create an issue in this repository
- Check the documentation in the `docs/` directory
- Review the troubleshooting guide

## 🔄 Roadmap

- [ ] Multi-exchange support (NSE, BSE)
- [ ] Advanced ML models for announcement classification
- [ ] Real-time dashboard and visualization
- [ ] Mobile app for monitoring
- [ ] Integration with more brokers

---

**Remember: Always test thoroughly in paper trading mode before deploying with real money!** 