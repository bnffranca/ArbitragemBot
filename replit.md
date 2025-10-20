# ArbitragemBot - MEXC Cryptocurrency Arbitrage Bot

## Overview
This is a cryptocurrency arbitrage bot that monitors and executes triangular arbitrage opportunities on the MEXC exchange. The bot continuously scans for profitable trading cycles (e.g., USDT → BTC → ETH → USDT) and automatically executes trades when opportunities meeting minimum spread requirements are found.

## Recent Changes
- **2025-10-20**: Initial Replit environment setup
  - Fixed corrupted main.py file 
  - Migrated hardcoded secrets to environment variables for security
  - Created requirements.txt for dependency management
  - Added Python .gitignore
  - Set up workflow for running the bot

## Project Architecture
### Files
- **main.py**: Entry point that runs the bot in a continuous loop with error handling
- **arbitragem_bot.py**: Core bot logic containing:
  - Market scanning and opportunity detection
  - Triangular arbitrage execution
  - Telegram notifications
  - Balance tracking and profit calculation
- **secrets.py**: Environment variable definitions (not actively used but kept for reference)
- **requirements.txt**: Python dependencies (ccxt, requests)

### Key Features
- Triangular arbitrage detection across MEXC spot markets
- Configurable minimum spread and volume thresholds
- Automatic trade execution when profitable opportunities are found
- Telegram notifications for executed trades and errors
- Real-time balance and profit tracking
- Error handling with automatic unwinding of positions

## Configuration
The bot requires the following environment variables:
- **MEXC_API_KEY**: Your MEXC exchange API key
- **MEXC_SECRET_KEY**: Your MEXC exchange secret key
- **TELEGRAM_TOKEN**: Telegram bot token for notifications
- **CHAT_ID**: Your Telegram chat ID for receiving notifications

### Trading Parameters (in arbitragem_bot.py)
- `SPREAD_MIN`: Minimum net spread percentage required (default: 0.5%)
- `VOLUME_MIN`: Minimum 24h volume in USDT (default: 800)
- `DELAY`: Delay between scans when no opportunity found (default: 0.2s)
- `USE_BALANCE_PCT`: Percentage of available balance to use per trade (default: 100%)
- `TOTAL_FEE`: Combined trading fees (default: 0.3%)

## How to Run
1. Set up the required environment variables (API keys and Telegram credentials)
2. Click "Run" to start the bot
3. The bot will continuously scan for arbitrage opportunities and execute profitable trades

## Important Notes
- This bot trades with real funds - use at your own risk
- Ensure you have sufficient USDT balance on MEXC
- Monitor the console output and Telegram notifications for bot activity
- The bot uses 100% of available USDT balance by default - adjust `USE_BALANCE_PCT` if needed
- All secrets have been moved to environment variables for security

## Dependencies
- Python 3.11
- ccxt: Cryptocurrency exchange library
- requests: HTTP library for Telegram notifications
