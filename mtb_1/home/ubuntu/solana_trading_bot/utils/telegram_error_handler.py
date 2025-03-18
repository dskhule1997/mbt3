"""
Telegram API error handler for Solana Trading Bot.
This module provides specific error handling for Telegram API errors.
"""
import asyncio
from telethon import errors
from loguru import logger

from utils.error_handler import ErrorHandler
from utils.rate_limiter import RateLimiter

class TelegramErrorHandler:
    """
    Telegram API error handler.
    Provides specific error handling for Telegram API errors.
    """
    
    # Common Telegram API errors and their retry strategies
    FLOOD_WAIT_ERRORS = (
        errors.FloodWaitError,
        errors.FloodError,
    )
    
    NETWORK_ERRORS = (
        errors.ServerError,
        errors.TimedOutError,
        errors.DisconnectedError,
        ConnectionError,
        asyncio.TimeoutError,
    )
    
    AUTHORIZATION_ERRORS = (
        errors.AuthKeyError,
        errors.SessionPasswordNeededError,
        errors.PhoneCodeInvalidError,
    )
    
    GROUP_ERRORS = (
        errors.ChatAdminRequiredError,
        errors.ChatWriteForbiddenError,
        errors.ChannelPrivateError,
        errors.InviteHashInvalidError,
        errors.InviteHashExpiredError,
    )
    
    @staticmethod
    def handle_telegram_errors(func=None, notify_admin=False, admin_notifier=None):
        """
        Decorator to handle Telegram API errors.
        
        Args:
            func: Function to decorate
            notify_admin: Whether to notify admin about the error
            admin_notifier: Function to notify admin
        
        Returns:
            Decorated function
        """
        return ErrorHandler.handle_exceptions(
            func=func,
            exceptions=(errors.RPCError, ConnectionError, asyncio.TimeoutError),
            log_level="ERROR",
            notify_admin=notify_admin,
            admin_notifier=admin_notifier
        )
    
    @staticmethod
    def handle_flood_wait(func=None, notify_admin=False, admin_notifier=None):
        """
        Decorator to handle Telegram flood wait errors.
        
        Args:
            func: Function to decorate
            notify_admin: Whether to notify admin about the error
            admin_notifier: Function to notify admin
        
        Returns:
            Decorated function
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except TelegramErrorHandler.FLOOD_WAIT_ERRORS as e:
                    # Get wait time
                    wait_time = getattr(e, 'seconds', 60)
                    
                    # Log error
                    logger.warning(f"Flood wait error in {func.__name__}: waiting for {wait_time} seconds")
                    
                    # Notify admin if requested
                    if notify_admin and admin_notifier:
                        try:
                            await admin_notifier(
                                f"⚠️ **Flood wait error in {func.__name__}**\n\n"
                                f"Waiting for {wait_time} seconds before retrying."
                            )
                        except Exception as notify_error:
                            logger.error(f"Failed to notify admin: {str(notify_error)}")
                    
                    # Wait and retry
                    await asyncio.sleep(wait_time)
                    return await func(*args, **kwargs)
                
                except Exception as e:
                    # Handle other exceptions
                    logger.error(f"Error in {func.__name__}: {str(e)}")
                    
                    # Notify admin if requested
                    if notify_admin and admin_notifier:
                        try:
                            await admin_notifier(
                                f"❌ **Error in {func.__name__}**\n\n"
                                f"```\n{str(e)}\n```"
                            )
                        except Exception as notify_error:
                            logger.error(f"Failed to notify admin: {str(notify_error)}")
                    
                    # Re-raise the exception
                    raise
            
            return wrapper
        
        # Handle case where decorator is used with or without arguments
        if func is None:
            return decorator
        return decorator(func)
    
    @staticmethod
    def retry_telegram_request(max_retries=3, retry_delay=5.0):
        """
        Decorator to retry Telegram API requests on failure.
        
        Args:
            max_retries: Maximum number of retries
            retry_delay: Delay between retries in seconds
        
        Returns:
            Decorated function
        """
        return ErrorHandler.retry(
            max_retries=max_retries,
            retry_delay=retry_delay,
            exceptions=TelegramErrorHandler.NETWORK_ERRORS,
            log_level="WARNING"
        )
    
    @staticmethod
    def rate_limit_telegram_request(rate_limit=20, per_seconds=60):
        """
        Decorator to limit the rate of Telegram API requests.
        
        Args:
            rate_limit: Maximum number of requests
            per_seconds: Time period in seconds
        
        Returns:
            Decorated function
        """
        return RateLimiter.limit_rate(
            rate_limit=rate_limit,
            per_seconds=per_seconds
        )

# Add missing imports
from functools import wraps
