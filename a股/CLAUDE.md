# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a comprehensive Chinese stock market analysis system (A股分析系统) based on the investment philosophy of "z哥" and his "少妇战法" (Young Woman Strategy). The system integrates data crawling, technical analysis, AI-powered analysis, and backtesting capabilities for Chinese A-share stocks.

## Core Architecture

### Main Modules

- **`src/web/app.py`** - Main Streamlit web application entry point
- **`config/unified_config.py`** - Unified configuration management system
- **`src/ai_analysis/`** - AI-powered stock analysis modules using Google Gemini API
- **`src/backtesting/`** - Complete backtesting system with multiple trading strategies
- **`src/crawling/`** - Data collection modules for stocks, market data, and indices
- **`src/cleaning/`** - Data cleaning and preprocessing modules
- **`src/talib_analysis/`** - Technical analysis using TA-Lib indicators
- **`src/web/components/`** - Streamlit page components for different analysis views

### Key Configuration Files

- **`config/unified_config.json`** - Main configuration file (API keys, model settings, etc.)
- **`config/strategy_configs.py`** - Trading strategy configurations
- **`config/ai_config.py`** - AI analysis configuration
- **`config/system_config.py`** - System-wide configuration

## Common Development Commands

### Running the Web Application
```bash
# Primary method - using the launcher script
python src/launchers/scripts/run_app.py

# Direct Streamlit execution
streamlit run src/web/app.py --server.port 8501
```

### Data Collection Pipelines
```bash
# Collect stock data
python src/launchers/scripts/run_data_pipeline_async.py

# Collect market data
python src/launchers/scripts/run_market_data_pipeline_async.py

# Collect index data
python src/launchers/scripts/run_index_pipeline_async.py
```

### AI Analysis Pipelines
```bash
# Individual stock AI analysis
python src/launchers/scripts/run_data_ai_pipeline_async.py

# Market-wide AI analysis
python src/launchers/scripts/run_market_ai_pipeline_async.py
```

### Backtesting Operations
```bash
# Run batch backtesting
python src/backtesting/launchers/run_batch_backtest.py

# Run parameter search
python src/backtesting/launchers/run_param_search.py
```

### Development Tools
```bash
# Install dependencies
pip install -r requirements.txt

# Code formatting (if available)
black src/
ruff check src/
mypy src/
```

## Data Flow Architecture

1. **Data Collection** (`src/crawling/`) → Raw market data from Chinese financial APIs
2. **Data Cleaning** (`src/cleaning/`) → Cleaned and standardized data
3. **Technical Analysis** (`src/talib_analysis/`) → Technical indicators and calculations
4. **AI Analysis** (`src/ai_analysis/`) → AI-powered insights using Gemini API
5. **Backtesting** (`src/backtesting/`) → Strategy testing and validation
6. **Web Interface** (`src/web/`) → Streamlit-based user interface

## Key Features & Systems

### "少妇战法" (Young Woman Strategy) Implementation
- **B1 Buy Point**: Multi-timeframe resonance strategy using weekly and monthly KDJ
- **B2 Buy Point**: Right-side strategy using daily KDJ, MACD, and 20-day moving average
- **3/4 Negative Volume Method**: Tool for identifying false breakouts
- **Price Filtering**: Intelligent B1 filtering to avoid chasing highs

### AI Analysis Integration
- Uses Google Gemini API for intelligent stock analysis
- Supports both individual stock and market-wide analysis
- Includes sentiment analysis, fundamental analysis, and technical recommendations
- Implements caching system for 6 core financial files

### Backtesting System
- Complete backtesting without look-ahead bias
- Support for multiple strategy types (Single, Double, Triple indicator combinations)
- Performance metrics and visualization
- Parameter optimization capabilities

## Configuration Notes

- API keys must be configured in `config/unified_config.json` before running AI analysis
- The system uses a unified configuration manager that supports environment variable overrides
- Default web server runs on port 8501
- Data files are stored in `data/` directory with organized subdirectories

## Development Guidelines

- The codebase uses Chinese comments and variable names extensively
- All date handling follows Chinese market calendar and trading hours
- Stock codes use Chinese market format (e.g., "000001.SZ" for Shenzhen, "600000.SH" for Shanghai)
- The system is designed specifically for Chinese A-share market analysis

## Testing

No specific test framework was detected in the codebase. Verify functionality by:
1. Running the web application and checking all components load
2. Executing data collection pipelines with sample stocks
3. Testing AI analysis with configured API keys
4. Running backtesting with default strategies