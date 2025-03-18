#!/usr/bin/env python3
"""
Test script for Solana Trading Bot.
This script tests the key components of the bot.
"""
import os
import sys
import asyncio
import argparse
from dotenv import load_dotenv
from loguru import logger

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import bot components
from utils.config import Config
from utils.logger import setup_logger
from telegram.user_client import UserClient
from telegram.bot_client import BotClient
from website_monitor.jup_monitor import JupTrenchesMonitor
from trading.solana_trader import SolanaTrader

async def test_telegram_group_joining(user_client):
    """Test Telegram group joining functionality."""
    print("\n=== Testing Telegram Group Joining ===")
    
    # Test public group joining
    public_group = input("Enter a public group username to test joining (e.g., 'solana'): ")
    if public_group:
        print(f"Attempting to join public group: {public_group}")
        try:
            result = await user_client.join_group(public_group)
            print(f"Result: {'Success' if result else 'Failed'}")
        except Exception as e:
            print(f"Error joining public group: {str(e)}")
    
    # Test private group joining
    private_group = input("Enter a private group invite link to test joining (or press Enter to skip): ")
    if private_group:
        print(f"Attempting to join private group: {private_group}")
        try:
            result = await user_client.join_group(private_group)
            print(f"Result: {'Success' if result else 'Failed'}")
        except Exception as e:
            print(f"Error joining private group: {str(e)}")
    
    return True

async def test_website_monitoring(jup_monitor):
    """Test website monitoring functionality."""
    print("\n=== Testing Website Monitoring ===")
    
    if not jup_monitor:
        print("Website monitoring is disabled in config. Skipping test.")
        return True
    
    print("Starting website monitor...")
    jup_monitor.start()
    
    # Set a test callback
    async def test_callback(token_data):
        print(f"Token detected: {token_data['symbol']} ({token_data['address']})")
    
    jup_monitor.set_notification_callback(test_callback)
    
    print("Monitoring jup.ag/trenches for 60 seconds...")
    print("This will test if the website loads correctly and tokens can be extracted.")
    
    # Wait for a minute to see if any tokens are detected
    for i in range(60):
        await asyncio.sleep(1)
        sys.stdout.write(f"\rWaiting: {i+1}/60 seconds")
        sys.stdout.flush()
    
    print("\nStopping website monitor...")
    jup_monitor.stop()
    
    return True

async def test_bot_interface(bot_client):
    """Test bot interface functionality."""
    print("\n=== Testing Bot Interface ===")
    
    admin_id = bot_client.admin_id
    print(f"Testing notification to admin (ID: {admin_id})")
    
    try:
        await bot_client.client.send_message(
            admin_id,
            "🧪 **Test Message**\n\nThis is a test message from the Solana Trading Bot test script."
        )
        print("Test message sent successfully!")
    except Exception as e:
        print(f"Error sending test message: {str(e)}")
        return False
    
    return True

async def test_trading_logic(trader):
    """Test trading logic functionality."""
    print("\n=== Testing Trading Logic ===")
    
    # Test wallet connection
    print("Testing wallet connection...")
    sol_balance = await trader.wallet.get_sol_balance()
    print(f"SOL Balance: {sol_balance}")
    
    # Test Jupiter API
    print("Testing Jupiter API connection...")
    test_token_address = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"  # USDC
    price = await trader.jupiter.get_price(test_token_address)
    print(f"USDC Price: {price if price is not None else 'Failed to get price'}")
    
    return True

async def main():
    """Main function to run the tests."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Solana Trading Bot Tests")
    parser.add_argument("--config", type=str, default=".env", help="Path to config file")
    parser.add_argument("--test", type=str, choices=["all", "telegram", "website", "bot", "trading"], 
                        default="all", help="Test to run")
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv(args.config)
    
    # Setup logger
    setup_logger()
    logger.info("Starting Solana Trading Bot Tests...")
    
    # Load configuration
    config = Config()
    logger.info("Configuration loaded successfully")
    
    try:
        # Initialize components based on test selection
        user_client = None
        bot_client = None
        jup_monitor = None
        trader = None
        
        if args.test in ["all", "telegram", "bot"]:
            # Initialize Telegram clients
            user_client = UserClient(
                api_id=config.user_api_id,
                api_hash=config.user_api_hash,
                phone=config.user_phone
            )
            
            await user_client.start()
            
            if args.test in ["all", "bot"]:
                bot_client = BotClient(
                    token=config.bot_token,
                    admin_id=config.admin_id,
                    user_client=user_client
                )
                
                await bot_client.start()
        
        if args.test in ["all", "website"]:
            # Initialize website monitor
            jup_monitor = JupTrenchesMonitor(
                url=config.jup_trenches_url,
                interval=config.monitoring_interval
            )
        
        if args.test in ["all", "trading"]:
            # Initialize trader
            trader = SolanaTrader(
                private_key=config.solana_private_key,
                rpc_url=config.solana_rpc_url,
                buy_amount=config.buy_amount_sol,
                target_multiplier=config.target_multiplier,
                sell_percentage=config.sell_percentage,
                auto_trade_enabled=False  # Disable auto-trading for tests
            )
        
        # Run selected tests
        results = {}
        
        if args.test in ["all", "telegram"] and user_client:
            results["telegram"] = await test_telegram_group_joining(user_client)
        
        if args.test in ["all", "website"] and jup_monitor:
            results["website"] = await test_website_monitoring(jup_monitor)
        
        if args.test in ["all", "bot"] and bot_client:
            results["bot"] = await test_bot_interface(bot_client)
        
        if args.test in ["all", "trading"] and trader:
            results["trading"] = await test_trading_logic(trader)
        
        # Print summary
        print("\n=== Test Summary ===")
        for test, result in results.items():
            print(f"{test.capitalize()}: {'PASS' if result else 'FAIL'}")
        
        # Check if all tests passed
        all_passed = all(results.values())
        print(f"\nOverall: {'PASS' if all_passed else 'FAIL'}")
    
    except Exception as e:
        logger.error(f"Error in tests: {str(e)}")
        print(f"\nError: {str(e)}")
    
    finally:
        # Cleanup
        if user_client:
            await user_client.stop()
        
        if bot_client:
            await bot_client.stop()
        
        if jup_monitor:
            jup_monitor.stop()
        
        logger.info("Tests completed")

if __name__ == "__main__":
    asyncio.run(main())
