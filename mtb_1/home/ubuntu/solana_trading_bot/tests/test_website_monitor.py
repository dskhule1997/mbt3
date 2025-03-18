#!/usr/bin/env python3
"""
Test script for website monitoring functionality.
This script specifically tests the ability to scrape and detect tokens from jup.ag/trenches.
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
from website_monitor.jup_monitor import JupTrenchesMonitor
from website_monitor.token_model import Token

async def test_website_loading(jup_monitor):
    """Test if the website loads correctly."""
    print("\n=== Testing Website Loading ===")
    
    print("Initializing browser and loading jup.ag/trenches...")
    try:
        await jup_monitor.initialize_browser()
        print("Browser initialized successfully")
        
        await jup_monitor.load_page()
        print("Page loaded successfully")
        
        # Take a screenshot for verification
        screenshot_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "jup_trenches_test.png")
        os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
        
        await jup_monitor.take_screenshot(screenshot_path)
        print(f"Screenshot saved to: {screenshot_path}")
        
        return True
    except Exception as e:
        print(f"Error loading website: {str(e)}")
        return False
    finally:
        await jup_monitor.close_browser()

async def test_token_extraction(jup_monitor):
    """Test if tokens can be extracted from the website."""
    print("\n=== Testing Token Extraction ===")
    
    try:
        await jup_monitor.initialize_browser()
        await jup_monitor.load_page()
        
        print("Extracting tokens from page...")
        tokens = await jup_monitor.extract_tokens()
        
        if not tokens:
            print("No tokens extracted. This might indicate an issue with the extraction logic.")
            return False
        
        print(f"Successfully extracted {len(tokens)} tokens:")
        for i, token in enumerate(tokens[:5]):  # Show first 5 tokens
            print(f"{i+1}. {token.symbol} ({token.address}): {token.price}")
        
        if len(tokens) > 5:
            print(f"... and {len(tokens) - 5} more tokens")
        
        return True
    except Exception as e:
        print(f"Error extracting tokens: {str(e)}")
        return False
    finally:
        await jup_monitor.close_browser()

async def test_new_token_detection(jup_monitor):
    """Test if new tokens can be detected."""
    print("\n=== Testing New Token Detection ===")
    
    try:
        # Create a test callback
        detected_tokens = []
        
        async def test_callback(token_data):
            detected_tokens.append(token_data)
            print(f"New token detected: {token_data['symbol']} ({token_data['address']})")
        
        jup_monitor.set_notification_callback(test_callback)
        
        # First run to establish baseline
        print("First run to establish baseline of known tokens...")
        await jup_monitor.initialize_browser()
        await jup_monitor.load_page()
        tokens1 = await jup_monitor.extract_tokens()
        await jup_monitor.close_browser()
        
        if not tokens1:
            print("No tokens extracted in first run. Cannot continue test.")
            return False
        
        print(f"Extracted {len(tokens1)} tokens in first run")
        
        # Create a fake "new" token by modifying one from the first batch
        if tokens1:
            # Take the first token and modify it to simulate a new token
            fake_token = Token(
                symbol=f"TEST_{tokens1[0].symbol}",
                address=tokens1[0].address,
                price=tokens1[0].price,
                volume=tokens1[0].volume,
                market_cap=tokens1[0].market_cap
            )
            
            # Add the fake token to the second batch
            print("Simulating a new token detection...")
            
            # Override the extract_tokens method temporarily
            original_extract = jup_monitor.extract_tokens
            
            async def mock_extract_tokens():
                tokens = await original_extract()
                tokens.append(fake_token)
                return tokens
            
            jup_monitor.extract_tokens = mock_extract_tokens
            
            # Run the monitor once
            print("Running monitor with simulated new token...")
            await jup_monitor.check_for_new_tokens()
            
            # Restore original method
            jup_monitor.extract_tokens = original_extract
            
            # Check if our fake token was detected
            detected = any(t['symbol'] == fake_token.symbol for t in detected_tokens)
            print(f"Fake token detection: {'Success' if detected else 'Failed'}")
            
            return detected
        
        return False
    except Exception as e:
        print(f"Error in new token detection test: {str(e)}")
        return False
    finally:
        await jup_monitor.close_browser()

async def test_continuous_monitoring(jup_monitor):
    """Test continuous monitoring for a short period."""
    print("\n=== Testing Continuous Monitoring ===")
    
    try:
        # Create a test callback
        detected_tokens = []
        
        async def test_callback(token_data):
            detected_tokens.append(token_data)
            print(f"New token detected: {token_data['symbol']} ({token_data['address']})")
        
        jup_monitor.set_notification_callback(test_callback)
        
        # Start the monitor
        print("Starting continuous monitoring for 2 minutes...")
        print("This will test if the monitor can run continuously without errors.")
        
        # Set a shorter interval for testing
        jup_monitor.interval = 30  # Check every 30 seconds
        jup_monitor.start()
        
        # Wait for 2 minutes
        for i in range(120):
            await asyncio.sleep(1)
            sys.stdout.write(f"\rWaiting: {i+1}/120 seconds")
            sys.stdout.flush()
        
        # Stop the monitor
        print("\nStopping monitor...")
        jup_monitor.stop()
        
        print(f"Detected {len(detected_tokens)} new tokens during monitoring")
        return True
    except Exception as e:
        print(f"Error in continuous monitoring test: {str(e)}")
        return False
    finally:
        if jup_monitor.is_running:
            jup_monitor.stop()

async def main():
    """Main function to run the tests."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Website Monitoring Tests")
    parser.add_argument("--config", type=str, default=".env", help="Path to config file")
    parser.add_argument("--test", type=str, choices=["all", "loading", "extraction", "detection", "monitoring"], 
                        default="all", help="Test to run")
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv(args.config)
    
    # Setup logger
    setup_logger()
    logger.info("Starting Website Monitoring Tests...")
    
    # Load configuration
    config = Config()
    logger.info("Configuration loaded successfully")
    
    try:
        # Initialize website monitor
        jup_monitor = JupTrenchesMonitor(
            url=config.jup_trenches_url,
            interval=config.monitoring_interval
        )
        
        # Run selected tests
        results = {}
        
        if args.test in ["all", "loading"]:
            results["website_loading"] = await test_website_loading(jup_monitor)
        
        if args.test in ["all", "extraction"]:
            results["token_extraction"] = await test_token_extraction(jup_monitor)
        
        if args.test in ["all", "detection"]:
            results["new_token_detection"] = await test_new_token_detection(jup_monitor)
        
        if args.test in ["all", "monitoring"]:
            results["continuous_monitoring"] = await test_continuous_monitoring(jup_monitor)
        
        # Print summary
        print("\n=== Test Summary ===")
        for test, result in results.items():
            print(f"{test.replace('_', ' ').title()}: {'PASS' if result else 'FAIL'}")
        
        # Check if all tests passed
        all_passed = all(results.values())
        print(f"\nOverall: {'PASS' if all_passed else 'FAIL'}")
    
    except Exception as e:
        logger.error(f"Error in tests: {str(e)}")
        print(f"\nError: {str(e)}")
    
    finally:
        # Cleanup
        if jup_monitor and jup_monitor.is_running:
            jup_monitor.stop()
        
        logger.info("Tests completed")

if __name__ == "__main__":
    asyncio.run(main())
