"""
User client for Telegram integration.
This module handles joining and monitoring Telegram groups using a user account.
"""
import asyncio
import os
from typing import Callable, Dict, List, Optional, Set
from telethon import TelegramClient
from loguru import logger

from telegram.client_factory import TelegramClientFactory
from telegram.group_manager import TelegramGroupManager
from telegram.message_handler import TelegramMessageHandler

class UserClient:
    """
    User client for Telegram integration.
    Uses a user account to join and monitor Telegram groups.
    """
    
    def __init__(self, api_id: int, api_hash: str, phone: str):
        """
        Initialize the user client.
        
        Args:
            api_id: API ID from my.telegram.org
            api_hash: API hash from my.telegram.org
            phone: Phone number associated with the user account
        """
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone = phone
        self.client = None
        self.session_string = None
        self.group_manager = None
        self.message_handler = None
        self.notification_callback = None
        self.running = False
        
        # Session file path
        self.session_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "config",
            "user_session.txt"
        )
        
        logger.info("User client initialized")
    
    async def start(self):
        """Start the user client and connect to Telegram."""
        logger.info("Starting user client...")
        
        # Load session if exists
        self.session_string = TelegramClientFactory.load_session(self.session_file)
        
        # Create client
        self.client, self.session_string = await TelegramClientFactory.create_user_client(
            api_id=self.api_id,
            api_hash=self.api_hash,
            phone=self.phone,
            session_string=self.session_string
        )
        
        # Save session
        TelegramClientFactory.save_session(self.session_string, self.session_file)
        
        # Initialize group manager and message handler
        self.group_manager = TelegramGroupManager(self.client)
        self.message_handler = TelegramMessageHandler(self.client)
        
        # Set notification callback for message handler
        if self.notification_callback:
            self.message_handler.set_notification_callback(self.notification_callback)
        
        logger.info("User client started successfully")
        
        # Get account info for logging
        me = await self.client.get_me()
        logger.info(f"Logged in as: {me.first_name} (ID: {me.id})")
    
    async def stop(self):
        """Stop the user client and disconnect from Telegram."""
        logger.info("Stopping user client...")
        
        if self.client:
            await self.client.disconnect()
        
        logger.info("User client stopped successfully")
    
    async def run(self):
        """Run the user client in a loop."""
        self.running = True
        logger.info("User client is now running")
        
        # Get joined groups and add them to monitored groups
        if self.group_manager and self.message_handler:
            groups = await self.group_manager.get_joined_groups()
            for group in groups:
                self.message_handler.add_monitored_group(group['id'])
                logger.info(f"Monitoring group: {group['title']}")
        
        while self.running:
            await asyncio.sleep(1)
    
    def set_notification_callback(self, callback: Callable):
        """
        Set the callback function for token notifications.
        
        Args:
            callback: Function to call when a token is detected
        """
        self.notification_callback = callback
        
        # Also set it for message handler if initialized
        if self.message_handler:
            self.message_handler.set_notification_callback(callback)
        
        logger.info("Notification callback set for user client")
    
    async def join_group(self, group_link: str) -> bool:
        """
        Join a Telegram group using an invite link.
        
        Args:
            group_link: Invite link for the group
        
        Returns:
            bool: True if joined successfully, False otherwise
        """
        if not self.group_manager:
            logger.error("Group manager not initialized")
            return False
        
        # Join the group
        group_info = await self.group_manager.join_group(group_link)
        
        if group_info:
            # Add to monitored groups
            if self.message_handler:
                self.message_handler.add_monitored_group(group_info['id'])
            
            # Scan recent messages
            if self.message_handler:
                await self.message_handler.scan_recent_messages(group_info['id'])
            
            return True
        
        return False
    
    async def leave_group(self, group_id: int) -> bool:
        """
        Leave a Telegram group.
        
        Args:
            group_id: ID of the group to leave
        
        Returns:
            bool: True if left successfully, False otherwise
        """
        if not self.group_manager:
            logger.error("Group manager not initialized")
            return False
        
        # Remove from monitored groups
        if self.message_handler:
            self.message_handler.remove_monitored_group(group_id)
        
        # Leave the group
        return await self.group_manager.leave_group(group_id)
    
    async def get_joined_groups(self) -> List[Dict]:
        """
        Get a list of all joined groups.
        
        Returns:
            List[Dict]: List of group information dictionaries
        """
        if not self.group_manager:
            logger.error("Group manager not initialized")
            return []
        
        return await self.group_manager.get_joined_groups()
