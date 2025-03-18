"""
Message handler for Telegram integration.
This module handles monitoring and processing messages from Telegram groups.
"""
import re
import asyncio
from typing import Callable, Dict, List, Optional, Set
from telethon import TelegramClient, events
from telethon.tl.types import Message, PeerChannel, PeerChat, PeerUser
from loguru import logger

class TelegramMessageHandler:
    """
    Handler for Telegram messages.
    Monitors and processes messages from Telegram groups.
    """
    
    def __init__(self, client: TelegramClient):
        """
        Initialize the message handler.
        
        Args:
            client: Telethon client instance (user client)
        """
        self.client = client
        self.notification_callback = None
        self.monitored_groups = set()
        self.token_pattern = re.compile(r'(\$[A-Z0-9]{2,10}|[A-Z0-9]{2,10})')
        self.address_pattern = re.compile(r'(0x[a-fA-F0-9]{40})')
        
        # Setup message handler
        self.client.add_event_handler(
            self._handle_new_message,
            events.NewMessage(incoming=True)
        )
        
        logger.info("Telegram message handler initialized")
    
    def set_notification_callback(self, callback: Callable):
        """
        Set the callback function for token notifications.
        
        Args:
            callback: Function to call when a token is detected
        """
        self.notification_callback = callback
        logger.info("Notification callback set for message handler")
    
    def add_monitored_group(self, group_id: int):
        """
        Add a group to the monitored groups list.
        
        Args:
            group_id: ID of the group to monitor
        """
        self.monitored_groups.add(group_id)
        logger.info(f"Added group {group_id} to monitored groups")
    
    def remove_monitored_group(self, group_id: int):
        """
        Remove a group from the monitored groups list.
        
        Args:
            group_id: ID of the group to stop monitoring
        """
        if group_id in self.monitored_groups:
            self.monitored_groups.remove(group_id)
            logger.info(f"Removed group {group_id} from monitored groups")
    
    async def _handle_new_message(self, event):
        """
        Handle new messages in monitored groups.
        
        Args:
            event: Telegram event containing the message
        """
        try:
            # Get message
            message = event.message
            
            # Skip empty messages
            if not message.text:
                return
            
            # Get chat ID
            chat = await event.get_chat()
            chat_id = chat.id
            
            # Check if this is a monitored group
            if self.monitored_groups and chat_id not in self.monitored_groups:
                return
            
            # Process the message
            await self._process_message(message, chat)
        
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
    
    async def _process_message(self, message: Message, chat):
        """
        Process a message for token mentions.
        
        Args:
            message: Telegram message
            chat: Chat where the message was sent
        """
        try:
            # Extract text
            text = message.text
            
            # Extract potential token symbols
            tokens = self.token_pattern.findall(text)
            addresses = self.address_pattern.findall(text)
            
            # If tokens or addresses found, notify
            if tokens or addresses:
                # Get sender info
                sender = await message.get_sender()
                sender_name = getattr(sender, 'first_name', 'Unknown')
                
                logger.info(f"Potential token mention in {getattr(chat, 'title', 'Unknown')} from {sender_name}: {tokens or addresses}")
                
                # Call notification callback if set
                if self.notification_callback:
                    for token in tokens:
                        # Clean token symbol (remove $ if present)
                        token = token.strip('$')
                        
                        # Create token info
                        token_info = {
                            'symbol': token,
                            'address': addresses[0] if addresses else None,
                            'source': f"Telegram: {getattr(chat, 'title', 'Unknown')}",
                            'message': text
                        }
                        
                        # Send notification
                        await self.notification_callback(token_info)
        
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
    
    async def scan_recent_messages(self, group_id: int, limit: int = 100):
        """
        Scan recent messages in a group for token mentions.
        
        Args:
            group_id: ID of the group to scan
            limit: Maximum number of messages to scan
        """
        logger.info(f"Scanning recent messages in group {group_id}")
        
        try:
            # Get the group entity
            group = await self.client.get_entity(group_id)
            
            # Get recent messages
            messages = await self.client.get_messages(group, limit=limit)
            
            # Process each message
            for message in messages:
                if message.text:
                    await self._process_message(message, group)
            
            logger.info(f"Scanned {len(messages)} messages in group {getattr(group, 'title', 'Unknown')}")
        
        except Exception as e:
            logger.error(f"Error scanning messages in group {group_id}: {str(e)}")
