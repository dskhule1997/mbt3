#!/usr/bin/env python3
"""
Test script for Telegram group joining functionality.
This script specifically tests the ability to join both public and private groups.
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
from telegram.group_manager import GroupManager

async def test_public_group_joining(user_client, group_manager):
    """Test joining a public Telegram group."""
    print("\n=== Testing Public Group Joining ===")
    
    public_group = input("Enter a public group username to test joining (e.g., 'solana'): ")
    if not public_group:
        print("Skipping public group test.")
        return None
    
    print(f"Attempting to join public group: {public_group}")
    try:
        # Try joining via user client directly
        result1 = await user_client.join_group(public_group)
        print(f"Direct join result: {'Success' if result1 else 'Failed'}")
        
        # Try joining via group manager
        result2 = await group_manager.join_group(public_group)
        print(f"Group manager join result: {'Success' if result2 else 'Failed'}")
        
        return result1 or result2
    except Exception as e:
        print(f"Error joining public group: {str(e)}")
        return False

async def test_private_group_joining(user_client, group_manager):
    """Test joining a private Telegram group via invite link."""
    print("\n=== Testing Private Group Joining ===")
    
    private_group = input("Enter a private group invite link to test joining (or press Enter to skip): ")
    if not private_group:
        print("Skipping private group test.")
        return None
    
    print(f"Attempting to join private group via invite link")
    try:
        # Try joining via user client directly
        result1 = await user_client.join_group(private_group)
        print(f"Direct join result: {'Success' if result1 else 'Failed'}")
        
        # Try joining via group manager
        result2 = await group_manager.join_group(private_group)
        print(f"Group manager join result: {'Success' if result2 else 'Failed'}")
        
        return result1 or result2
    except Exception as e:
        print(f"Error joining private group: {str(e)}")
        return False

async def test_group_message_monitoring(user_client, group_manager):
    """Test monitoring messages in joined groups."""
    print("\n=== Testing Group Message Monitoring ===")
    
    # Get list of joined groups
    groups = await user_client.get_dialogs()
    group_list = [g.entity.username or g.entity.title for g in groups if hasattr(g.entity, 'title') and g.entity.title]
    
    if not group_list:
        print("No groups found to monitor. Please join groups first.")
        return False
    
    print(f"Found {len(group_list)} groups/chats:")
    for i, group in enumerate(group_list):
        print(f"{i+1}. {group}")
    
    # Select a group to monitor
    selection = input(f"Enter group number to monitor (1-{len(group_list)}) or press Enter to skip: ")
    if not selection:
        print("Skipping message monitoring test.")
        return None
    
    try:
        index = int(selection) - 1
        if index < 0 or index >= len(group_list):
            print("Invalid selection.")
            return False
        
        selected_group = group_list[index]
        print(f"Monitoring messages in: {selected_group}")
        
        # Set up a test message handler
        async def test_message_handler(event):
            sender = await event.get_sender()
            sender_name = getattr(sender, 'username', None) or getattr(sender, 'first_name', 'Unknown')
            print(f"Message from {sender_name}: {event.text}")
        
        # Start monitoring
        user_client.add_event_handler(test_message_handler)
        
        print("Monitoring messages for 60 seconds...")
        print("Send messages to the selected group to test monitoring.")
        
        # Wait for a minute
        for i in range(60):
            await asyncio.sleep(1)
            sys.stdout.write(f"\rWaiting: {i+1}/60 seconds")
            sys.stdout.flush()
        
        # Remove the handler
        user_client.remove_event_handler(test_message_handler)
        print("\nMessage monitoring test completed.")
        
        return True
    except Exception as e:
        print(f"Error in message monitoring test: {str(e)}")
        return False

async def main():
    """Main function to run the tests."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Telegram Group Joining Tests")
    parser.add_argument("--config", type=str, default=".env", help="Path to config file")
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv(args.config)
    
    # Setup logger
    setup_logger()
    logger.info("Starting Telegram Group Joining Tests...")
    
    # Load configuration
    config = Config()
    logger.info("Configuration loaded successfully")
    
    try:
        # Initialize user client
        user_client = UserClient(
            api_id=config.user_api_id,
            api_hash=config.user_api_hash,
            phone=config.user_phone
        )
        
        # Start the client
        await user_client.start()
        logger.info("User client started successfully")
        
        # Initialize group manager
        group_manager = GroupManager(user_client)
        
        # Run tests
        results = {}
        
        # Test public group joining
        results["public_group"] = await test_public_group_joining(user_client, group_manager)
        
        # Test private group joining
        results["private_group"] = await test_private_group_joining(user_client, group_manager)
        
        # Test message monitoring
        results["message_monitoring"] = await test_group_message_monitoring(user_client, group_manager)
        
        # Print summary
        print("\n=== Test Summary ===")
        for test, result in results.items():
            if result is None:
                status = "SKIPPED"
            else:
                status = "PASS" if result else "FAIL"
            print(f"{test.replace('_', ' ').title()}: {status}")
        
        # Check if all tests passed
        all_passed = all(result is True or result is None for result in results.values())
        print(f"\nOverall: {'PASS' if all_passed else 'FAIL'}")
    
    except Exception as e:
        logger.error(f"Error in tests: {str(e)}")
        print(f"\nError: {str(e)}")
    
    finally:
        # Cleanup
        if user_client:
            await user_client.stop()
        
        logger.info("Tests completed")

if __name__ == "__main__":
    asyncio.run(main())
