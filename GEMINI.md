# GEMINI.md

## Project Overview

This project is a comprehensive stock analysis system designed for A-share stocks. It's built with Python and utilizes the Streamlit framework for its web interface. The system is based on the investment philosophy of a well-known investment blogger, "z哥," and incorporates his "少妇战法" (Young Woman Battle Tactic) investment strategy.

The application provides a wide range of features, including:

*   **Data Collection:** Fetches stock and market data from various sources like Akshare, Baostock, and Tushare.
*   **Technical Analysis:** Implements z哥's investment strategy, including B1 and B2 buying points, and other technical indicators using TA-Lib.
*   **Fundamental Analysis:** Provides financial data and analysis for individual stocks.
*   **AI-Powered Analysis:** Integrates with Google Gemini and OpenAI APIs to provide intelligent analysis of stocks and the market.
*   **Backtesting:** A complete backtesting engine to test trading strategies without look-ahead bias.
*   **Web Interface:** A user-friendly web interface built with Streamlit that visualizes data and analysis results.

The project is well-structured, with a clear separation of concerns. It uses a unified configuration system that allows for easy management of settings and API keys. The code is modular, with different functionalities organized into separate packages.

## Building and Running

To build and run this project, you need to have Python and the required dependencies installed.

**1. Install Dependencies:**

```bash
pip install -r requirements.txt
```

**2. Configure the Application:**

The application uses a unified configuration file located at `config/unified_config.json`. You can create this file by copying the example file:

```bash
cp config/unified_config.json.example config/unified_config.json
```

Then, edit `config/unified_config.json` to add your API keys for data sources and AI services.

**3. Run the Data Pipeline:**

Before running the application, you need to fetch the necessary data. The project provides scripts to do this:

```bash
# Crawl stock data
python src/launchers/scripts/run_data_pipeline_async.py

# Crawl market data
python src/launchers/scripts/run_market_data_pipeline_async.py
```

**4. Run the AI Analysis:**

To generate AI-powered analysis, run the following scripts:

```bash
# Individual stock AI analysis
python src/launchers/scripts/run_data_ai_pipeline_async.py

# Market AI analysis
python src/launchers/scripts/run_market_ai_pipeline_async.py
```

**5. Start the Web Application:**

To start the Streamlit web application, run the following command:

```bash
streamlit run src/web/app.py
```

The application will be available at `http://localhost:8501`.

## Development Conventions

*   **Configuration:** The project uses a centralized configuration system in the `config` directory. All configuration is managed through the `UnifiedConfigManager`.
*   **Modularity:** The codebase is highly modular, with different functionalities organized into packages within the `src` directory.
*   **Asynchronous Operations:** The data collection and AI analysis pipelines use asynchronous operations (`asyncio`) for better performance.
*   **Caching:** The application uses a caching mechanism for financial data to improve performance.
*   **Styling:** The project uses a custom dark theme for the Streamlit application.
*   **Testing:** The project includes a `pytest` setup for testing, but no tests are currently implemented.
