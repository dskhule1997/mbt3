"""
Rate limiter for Telegram API requests.
This module provides rate limiting utilities to avoid hitting Telegram API limits.
"""
import asyncio
import time
from functools import wraps
from loguru import logger

class RateLimiter:
    """
    Rate limiter for Telegram API requests.
    Implements a token bucket algorithm to limit request rates.
    """
    
    def __init__(self, rate_limit=20, per_seconds=60):
        """
        Initialize the rate limiter.
        
        Args:
            rate_limit: Maximum number of requests
            per_seconds: Time period in seconds
        """
        self.rate_limit = rate_limit
        self.per_seconds = per_seconds
        self.tokens = rate_limit
        self.last_refill = time.time()
        self.lock = asyncio.Lock()
    
    async def _refill_tokens(self):
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        
        # Calculate tokens to add
        new_tokens = elapsed * (self.rate_limit / self.per_seconds)
        
        # Update tokens and last refill time
        self.tokens = min(self.tokens + new_tokens, self.rate_limit)
        self.last_refill = now
    
    async def acquire(self):
        """
        Acquire a token for making a request.
        Blocks until a token is available.
        """
        async with self.lock:
            await self._refill_tokens()
            
            # If no tokens available, wait until we have one
            if self.tokens < 1:
                # Calculate wait time
                wait_time = (1 - self.tokens) * (self.per_seconds / self.rate_limit)
                logger.debug(f"Rate limit reached, waiting {wait_time:.2f} seconds")
                
                # Release lock while waiting
                self.lock.release()
                await asyncio.sleep(wait_time)
                await self.lock.acquire()
                
                # Refill tokens after waiting
                await self._refill_tokens()
            
            # Consume a token
            self.tokens -= 1
    
    @staticmethod
    def limit_rate(rate_limit=20, per_seconds=60):
        """
        Decorator to limit the rate of function calls.
        
        Args:
            rate_limit: Maximum number of requests
            per_seconds: Time period in seconds
        
        Returns:
            Decorated function
        """
        limiter = RateLimiter(rate_limit, per_seconds)
        
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                await limiter.acquire()
                return await func(*args, **kwargs)
            return wrapper
        
        return decorator
