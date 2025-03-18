"""
Website monitor base class for monitoring websites.
This module provides a base class for website monitors.
"""
import asyncio
import time
import threading
from abc import ABC, abstractmethod
from typing import Callable, Dict, List, Optional, Set
from datetime import datetime
from loguru import logger

from website_monitor.token_model import Token

class BaseWebsiteMonitor(ABC):
    """
    Base class for website monitors.
    Provides common functionality for monitoring websites.
    """
    
    def __init__(self, url: str, interval: int = 60):
        """
        Initialize the website monitor.
        
        Args:
            url: URL of the website to monitor
            interval: Monitoring interval in seconds
        """
        self.url = url
        self.interval = interval
        self.notification_callback = None
        self.running = False
        self.thread = None
        
        # Store known tokens to detect new ones
        self.known_tokens = set()
        self.last_check_time = None
        
        logger.info(f"Website monitor initialized for {url}")
    
    def start(self):
        """Start the website monitor."""
        logger.info(f"Starting website monitor for {self.url}...")
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop)
        self.thread.daemon = True
        self.thread.start()
        logger.info("Website monitor started successfully")
    
    def stop(self):
        """Stop the website monitor."""
        logger.info("Stopping website monitor...")
        self.running = False
        if self.thread:
            self.thread.join(timeout=10)
        logger.info("Website monitor stopped successfully")
    
    async def run(self):
        """Run the website monitor in a loop."""
        while self.running:
            await asyncio.sleep(1)
    
    def set_notification_callback(self, callback: Callable):
        """
        Set the callback function for token notifications.
        
        Args:
            callback: Function to call when a token is detected
        """
        self.notification_callback = callback
        logger.info("Notification callback set for website monitor")
    
    def _monitor_loop(self):
        """Monitor loop for checking the website periodically."""
        try:
            # Initialize the monitor
            self._initialize()
            
            # Main monitoring loop
            while self.running:
                try:
                    self._check_website()
                    self.last_check_time = datetime.now()
                    time.sleep(self.interval)
                except Exception as e:
                    logger.error(f"Error checking website: {str(e)}")
                    time.sleep(self.interval)
        
        except Exception as e:
            logger.error(f"Error in monitor loop: {str(e)}")
        
        finally:
            # Clean up
            self._cleanup()
    
    def _check_website(self):
        """Check the website for new tokens."""
        logger.info(f"Checking {self.url} for new tokens...")
        
        try:
            # Extract token information
            tokens = self._extract_tokens()
            
            # Check for new tokens
            new_tokens = self._detect_new_tokens(tokens)
            
            # Notify about new tokens
            if new_tokens and self.notification_callback:
                logger.info(f"Found {len(new_tokens)} new tokens")
                
                # Create event loop for async callback
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Notify about each new token
                for token in new_tokens:
                    try:
                        loop.run_until_complete(self.notification_callback(token.to_dict()))
                    except Exception as e:
                        logger.error(f"Error notifying about token {token.symbol}: {str(e)}")
                
                loop.close()
            
            logger.info("Website check completed")
        
        except Exception as e:
            logger.error(f"Error checking website: {str(e)}")
    
    def _detect_new_tokens(self, tokens: List[Token]) -> List[Token]:
        """
        Detect new tokens that haven't been seen before.
        
        Args:
            tokens: List of tokens
        
        Returns:
            List of new tokens
        """
        new_tokens = []
        current_symbols = set()
        
        for token in tokens:
            symbol = token.symbol
            current_symbols.add(symbol)
            
            if symbol not in self.known_tokens:
                logger.info(f"New token detected: {symbol}")
                new_tokens.append(token)
        
        # Update known tokens
        self.known_tokens = current_symbols
        
        return new_tokens
    
    @abstractmethod
    def _initialize(self):
        """Initialize the monitor. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def _cleanup(self):
        """Clean up resources. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def _extract_tokens(self) -> List[Token]:
        """
        Extract token information from the website.
        Must be implemented by subclasses.
        
        Returns:
            List of tokens
        """
        pass
