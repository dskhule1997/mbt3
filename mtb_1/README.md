# Solana Trading Bot

A complete Telegram-based Solana trading bot that monitors both Telegram groups and the jup.ag/trenches website for new tokens, and executes trades automatically.

## Features

- **Dual-Client Telegram Architecture**
  - User client for joining and monitoring Telegram groups
  - Bot client for handling commands and sending notifications
  - Robust group joining for both public and private groups

- **Website Monitoring**
  - Selenium-based monitoring of jup.ag/trenches
  - Dynamic content loading with proper waits
  - Token extraction with address, price, and metrics
  - New token detection mechanism

- **Trading Logic**
  - Automatic token buying with configurable SOL amount
  - Position monitoring until target profit is reached
  - Automatic selling at configurable percentage
  - Integration with Jupiter Aggregator for swaps

- **User Interface**
  - Clean, intuitive Telegram bot interface
  - Inline buttons for enabling/disabling auto-trading
  - Commands for configuring trading parameters
  - Status commands to check active positions

- **Error Handling & Logging**
  - Comprehensive error handling for all components
  - Detailed logging with component-specific loggers
  - Rate limiting for Telegram API
  - Automatic retries for network errors

## Architecture

The bot consists of several key components:

1. **Telegram Integration**
   - `user_client.py`: Handles joining and monitoring Telegram groups
   - `bot_client.py`: Manages bot commands and notifications
   - `interface.py`: Connects the bot with trading logic
   - `group_manager.py`: Manages group joining and monitoring
   - `message_handler.py`: Processes messages for token mentions

2. **Website Monitoring**
   - `jup_monitor.py`: Monitors jup.ag/trenches for new tokens
   - `token_model.py`: Data model for detected tokens
   - `base_monitor.py`: Base class for website monitors

3. **Trading Logic**
   - `solana_trader.py`: Handles buying, monitoring, and selling tokens
   - `wallet.py`: Manages Solana wallet operations
   - `jupiter_client.py`: Interacts with Jupiter Aggregator API
   - `trade_model.py`: Data model for active trades

4. **Utilities**
   - `config.py`: Loads and manages configuration
   - `logger.py`: Configures logging
   - `error_handler.py`: Provides error handling utilities
   - `rate_limiter.py`: Implements rate limiting for API calls
   - `telegram_error_handler.py`: Handles Telegram-specific errors
   - `selenium_error_handler.py`: Handles Selenium-specific errors

## Getting Started

See the [Setup Guide](SETUP_GUIDE.md) for detailed instructions on:
- Installing dependencies
- Obtaining API credentials
- Configuring the bot
- Running and using the bot
- Troubleshooting common issues

## Requirements

- Python 3.8+
- Telethon for Telegram API
- Selenium for website monitoring
- Solana Python SDK for blockchain interactions
- Additional dependencies listed in `requirements.txt`

## Disclaimer

This bot is provided for educational and personal use only. Trading cryptocurrencies involves significant risk. Use this bot at your own risk.
