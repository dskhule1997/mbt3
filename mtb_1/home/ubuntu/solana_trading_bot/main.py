#!/usr/bin/env python3
"""
Main entry point for the Solana Trading Bot.
This script initializes and runs all components of the bot.
"""
import asyncio
import os
import argparse
from dotenv import load_dotenv
from loguru import logger

# Import bot components
from telegram.user_client import UserClient
from telegram.bot_client import BotClient
from telegram.interface import TelegramInterface
from website_monitor.jup_monitor import JupTrenchesMonitor
from trading.solana_trader import SolanaTrader
from utils.config import Config
from utils.logger import setup_logger

async def main():
    """Main function to run the Solana Trading Bot."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Solana Trading Bot")
    parser.add_argument("--config", type=str, default=".env", help="Path to config file")
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv(args.config)
    
    # Setup logger
    setup_logger()
    logger.info("Starting Solana Trading Bot...")
    
    # Load configuration
    config = Config()
    logger.info("Configuration loaded successfully")
    
    try:
        # Initialize components
        user_client = UserClient(
            api_id=config.user_api_id,
            api_hash=config.user_api_hash,
            phone=config.user_phone
        )
        
        bot_client = BotClient(
            token=config.bot_token,
            admin_id=config.admin_id,
            user_client=user_client
        )
        
        trader = SolanaTrader(
            private_key=config.solana_private_key,
            rpc_url=config.solana_rpc_url,
            buy_amount=config.buy_amount_sol,
            target_multiplier=config.target_multiplier,
            sell_percentage=config.sell_percentage,
            auto_trade_enabled=config.auto_trade_enabled
        )
        
        # Initialize website monitor if enabled
        jup_monitor = None
        if config.enable_website_monitor:
            jup_monitor = JupTrenchesMonitor(
                url=config.jup_trenches_url,
                interval=config.monitoring_interval
            )
        
        # Initialize Telegram interface
        interface = TelegramInterface(
            bot_client=bot_client,
            trader=trader,
            jup_monitor=jup_monitor
        )
        
        # Start all components
        logger.info("Starting all components...")
        
        # Start the user client for monitoring Telegram groups
        await user_client.start()
        
        # Start the bot client for handling commands
        await bot_client.start()
        
        # Start the website monitor if enabled
        if jup_monitor:
            jup_monitor.start()
            logger.info("Website monitor started")
        
        # Start trade monitoring
        trader.start_monitoring()
        logger.info("Trade monitoring started")
        
        # Join configured Telegram groups
        for group in config.telegram_groups:
            await user_client.join_group(group)
        
        logger.info("Bot is now running. Press Ctrl+C to stop.")
        
        # Keep the bot running
        await asyncio.gather(
            user_client.run(),
            bot_client.run()
        )
    
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down...")
    
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
    
    finally:
        # Cleanup
        logger.info("Shutting down components...")
        
        # Stop website monitor
        if jup_monitor:
            jup_monitor.stop()
            logger.info("Website monitor stopped")
        
        # Stop trade monitoring
        trader.stop_monitoring()
        logger.info("Trade monitoring stopped")
        
        # Stop Telegram clients
        await bot_client.stop()
        await user_client.stop()
        
        logger.info("Bot stopped successfully")

if __name__ == "__main__":
    asyncio.run(main())
