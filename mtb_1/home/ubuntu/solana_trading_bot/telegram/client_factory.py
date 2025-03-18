"""
Telegram client factory for creating and managing Telegram clients.
This module provides a factory for creating both user and bot clients.
"""
import os
from typing import Optional, Tuple
from telethon import TelegramClient
from telethon.sessions import StringSession
from loguru import logger

class TelegramClientFactory:
    """
    Factory for creating and managing Telegram clients.
    Provides methods for creating both user and bot clients.
    """
    
    @staticmethod
    async def create_user_client(
        api_id: int,
        api_hash: str,
        phone: str,
        session_string: Optional[str] = None
    ) -> Tuple[TelegramClient, str]:
        """
        Create a user client for Telegram.
        
        Args:
            api_id: API ID from my.telegram.org
            api_hash: API hash from my.telegram.org
            phone: Phone number associated with the user account
            session_string: Optional session string for resuming session
        
        Returns:
            Tuple containing the client and session string
        """
        logger.info("Creating user client...")
        
        # Create session
        if session_string:
            session = StringSession(session_string)
            logger.info("Using existing session")
        else:
            session = StringSession()
            logger.info("Creating new session")
        
        # Create client
        client = TelegramClient(session, api_id, api_hash)
        
        # Start client
        await client.start(phone=phone)
        
        # Get session string for saving
        if not session_string:
            session_string = client.session.save()
            logger.info("New session created")
        
        # Get account info for logging
        me = await client.get_me()
        logger.info(f"User client created for: {me.first_name} (ID: {me.id})")
        
        return client, session_string
    
    @staticmethod
    async def create_bot_client(
        token: str,
        session_string: Optional[str] = None
    ) -> Tuple[TelegramClient, str]:
        """
        Create a bot client for Telegram.
        
        Args:
            token: Bot token from BotFather
            session_string: Optional session string for resuming session
        
        Returns:
            Tuple containing the client and session string
        """
        logger.info("Creating bot client...")
        
        # Extract API ID and hash from token (dummy values, will be overridden)
        api_id = 1
        api_hash = "1"
        
        # Create session
        if session_string:
            session = StringSession(session_string)
            logger.info("Using existing session")
        else:
            session = StringSession()
            logger.info("Creating new session")
        
        # Create client
        client = TelegramClient(session, api_id, api_hash)
        
        # Start client
        await client.start(bot_token=token)
        
        # Get session string for saving
        if not session_string:
            session_string = client.session.save()
            logger.info("New session created")
        
        # Get bot info for logging
        me = await client.get_me()
        logger.info(f"Bot client created for: {me.first_name} (@{me.username})")
        
        return client, session_string
    
    @staticmethod
    def save_session(session_string: str, filename: str) -> bool:
        """
        Save session string to file.
        
        Args:
            session_string: Session string to save
            filename: Filename to save to
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            # Save session string
            with open(filename, 'w') as f:
                f.write(session_string)
            
            logger.info(f"Session saved to {filename}")
            return True
        
        except Exception as e:
            logger.error(f"Error saving session: {str(e)}")
            return False
    
    @staticmethod
    def load_session(filename: str) -> Optional[str]:
        """
        Load session string from file.
        
        Args:
            filename: Filename to load from
        
        Returns:
            Session string if successful, None otherwise
        """
        try:
            # Check if file exists
            if not os.path.exists(filename):
                logger.warning(f"Session file {filename} does not exist")
                return None
            
            # Load session string
            with open(filename, 'r') as f:
                session_string = f.read().strip()
            
            logger.info(f"Session loaded from {filename}")
            return session_string
        
        except Exception as e:
            logger.error(f"Error loading session: {str(e)}")
            return None
