# Solana Trading Bot - Setup Guide

## Overview

This Solana Trading Bot is designed to monitor both Telegram groups and the jup.ag/trenches website for new Solana tokens, and execute trades automatically. It features a dual-client architecture for Telegram integration, robust website monitoring with Selenium, and automated trading functionality.

## Prerequisites

- Python 3.8 or higher
- A Telegram account with API access
- A Telegram bot created through BotFather
- A Solana wallet with SOL for trading
- Chrome or Chromium browser (for Selenium)

## Installation

1. Clone the repository or extract the provided files to your desired location:

```bash
git clone <repository-url>
cd solana-trading-bot
```

2. Create a virtual environment and activate it:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file by copying the provided `.env.example`:

```bash
cp .env.example .env
```

5. Configure the `.env` file with your credentials and settings (see Configuration section below).

## Obtaining API Credentials

### Telegram User API Credentials

To obtain your Telegram API ID and API Hash:

1. Visit [my.telegram.org](https://my.telegram.org/) and log in with your phone number.
2. Click on "API Development Tools".
3. Create a new application by filling in the required fields:
   - App title: Solana Trading Bot (or any name you prefer)
   - Short name: solana_bot (or any short name)
   - Platform: Desktop
   - Description: A bot for monitoring Telegram groups
4. Click on "Create Application".
5. You will receive your `API_ID` and `API_HASH`. Copy these values to your `.env` file.

### Telegram Bot Token

To create a Telegram bot and obtain a bot token:

1. Open Telegram and search for [@BotFather](https://t.me/BotFather).
2. Start a chat with BotFather and send the command `/newbot`.
3. Follow the instructions to create a new bot:
   - Provide a name for your bot (e.g., "Solana Trading Bot")
   - Provide a username for your bot (must end with "bot", e.g., "solana_trading_bot")
4. BotFather will provide you with a token. Copy this token to your `.env` file.

### Solana Wallet

To set up your Solana wallet:

1. If you don't have a Solana wallet, create one using [Phantom](https://phantom.app/) or [Solflare](https://solflare.com/).
2. Export your private key from your wallet (refer to your wallet's documentation for instructions).
3. Add your private key to the `.env` file.
4. Use a reliable RPC endpoint for Solana. You can use public endpoints or create an account with providers like [QuickNode](https://www.quicknode.com/) or [Alchemy](https://www.alchemy.com/) for better reliability.

## Configuration

Edit the `.env` file with your credentials and settings:

```
# Telegram User Client
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_PHONE=your_phone_number
TELEGRAM_SESSION_FILE=user_session

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_ADMIN_ID=your_telegram_id

# Telegram Groups to Monitor (comma-separated)
TELEGRAM_GROUPS=group1_username,group2_invite_link

# Solana Wallet
SOLANA_PRIVATE_KEY=your_private_key
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com

# Trading Settings
BUY_AMOUNT=0.1
TARGET_MULTIPLIER=2.0
SELL_PERCENTAGE=80.0
AUTO_TRADE_ENABLED=false

# Website Monitoring
ENABLE_WEBSITE_MONITOR=true
JUP_TRENCHES_URL=https://jup.ag/trenches?tab=trending
WEBSITE_CHECK_INTERVAL=60

# Logging
LOG_LEVEL=INFO
```

### Important Configuration Notes:

- `TELEGRAM_PHONE`: Your phone number in international format (e.g., +12345678901)
- `TELEGRAM_ADMIN_ID`: Your Telegram user ID (you can get it from [@userinfobot](https://t.me/userinfobot))
- `TELEGRAM_GROUPS`: List of groups to monitor, can be usernames or invite links
- `BUY_AMOUNT`: Amount of SOL to use for each trade
- `TARGET_MULTIPLIER`: Target profit multiplier (2.0 = 2x or 100% profit)
- `SELL_PERCENTAGE`: Percentage of position to sell when target is reached
- `AUTO_TRADE_ENABLED`: Whether to automatically trade detected tokens

## Running the Bot

To start the bot:

```bash
python main.py
```

You can also specify a custom config file:

```bash
python main.py --config custom_config.env
```

## Usage

Once the bot is running, you can interact with it through Telegram:

### Available Commands

- `/start` - Start the bot and show welcome message
- `/help` - Show available commands
- `/status` - Show bot status
- `/settings` - Show current settings
- `/trades` - Show active trades
- `/enable` - Enable auto-trading
- `/disable` - Disable auto-trading
- `/setbuy <amount>` - Set buy amount in SOL
- `/settarget <multiplier>` - Set target profit multiplier
- `/setsell <percentage>` - Set sell percentage at target

### Workflow

1. The bot monitors configured Telegram groups and the jup.ag/trenches website for new token mentions.
2. When a new token is detected, the bot sends a notification to the admin.
3. If auto-trading is enabled, the bot automatically buys the token with the configured amount of SOL.
4. The bot monitors the position until it reaches the target profit.
5. When the target is reached, the bot sells the configured percentage of the position.

## Troubleshooting

### Common Issues

#### Telegram Connection Issues

**Problem**: Bot fails to connect to Telegram API.
**Solution**: 
- Verify your API credentials in the `.env` file.
- Check your internet connection.
- If you see a flood wait error, wait for the specified time before retrying.

#### Session File Issues

**Problem**: Session file errors or authentication failures.
**Solution**:
- Delete the session file and restart the bot to create a new session.
- Ensure your phone number is in the correct international format.
- You may need to enter the verification code when prompted.

#### Website Monitoring Issues

**Problem**: Bot fails to detect tokens from jup.ag/trenches.
**Solution**:
- Check if Chrome/Chromium is installed correctly.
- Verify that the website structure hasn't changed.
- Check the logs for Selenium errors.
- Increase the wait time for page loading if necessary.

#### Trading Issues

**Problem**: Bot fails to execute trades.
**Solution**:
- Verify your Solana wallet private key and RPC URL.
- Ensure you have enough SOL in your wallet for trading.
- Check the logs for Jupiter API errors.

### Checking Logs

The bot creates detailed logs in the `logs` directory:
- Regular logs: `solana_bot_YYYYMMDD_HHMMSS.log`
- Error logs: `solana_bot_errors_YYYYMMDD_HHMMSS.log`

Review these logs to identify specific issues.

## Security Considerations

- **Private Key Security**: Your Solana private key is sensitive information. Never share your `.env` file or private key with anyone.
- **Telegram API Credentials**: Keep your API ID and API Hash confidential.
- **Bot Token**: Your bot token should be kept secure to prevent unauthorized access to your bot.
- **Risk Management**: Start with small trade amounts until you're comfortable with the bot's operation.

## Limitations

- The bot cannot join Telegram groups automatically that require admin approval.
- Website monitoring depends on the structure of jup.ag/trenches; if the website changes significantly, the monitoring may fail.
- Trading is simulated in the current implementation; to execute real trades, you would need to implement the actual transaction signing and submission.

## Support and Feedback

If you encounter any issues or have suggestions for improvements, please:
1. Check the troubleshooting section above
2. Review the logs for specific error messages
3. Contact the developer with detailed information about your issue

## Disclaimer

This bot is provided for educational and personal use only. Trading cryptocurrencies involves significant risk. Use this bot at your own risk. The developer is not responsible for any financial losses incurred through the use of this bot.
