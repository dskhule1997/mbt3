"""
Error handler for Solana Trading Bot.
This module provides error handling utilities for the bot.
"""
import sys
import traceback
from functools import wraps
from typing import Callable, Optional, Type, Union
from loguru import logger

class ErrorHandler:
    """
    Error handler for Solana Trading Bot.
    Provides utilities for handling errors and exceptions.
    """
    
    @staticmethod
    def handle_exceptions(
        func=None, 
        exceptions: Union[Type[Exception], tuple] = Exception,
        default_return=None,
        log_level: str = "ERROR",
        notify_admin: bool = False,
        admin_notifier: Optional[Callable] = None
    ):
        """
        Decorator to handle exceptions in functions.
        
        Args:
            func: Function to decorate
            exceptions: Exception type(s) to catch
            default_return: Default return value if exception occurs
            log_level: Log level for exceptions
            notify_admin: Whether to notify admin about the exception
            admin_notifier: Function to notify admin
        
        Returns:
            Decorated function
        """
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    # Get exception details
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    tb_str = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
                    
                    # Log exception
                    log_method = getattr(logger, log_level.lower())
                    log_method(f"Exception in {func.__name__}: {str(e)}\n{tb_str}")
                    
                    # Notify admin if requested
                    if notify_admin and admin_notifier:
                        try:
                            await admin_notifier(
                                f"❌ **Error in {func.__name__}**\n\n"
                                f"```\n{str(e)}\n```"
                            )
                        except Exception as notify_error:
                            logger.error(f"Failed to notify admin: {str(notify_error)}")
                    
                    return default_return
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    # Get exception details
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    tb_str = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
                    
                    # Log exception
                    log_method = getattr(logger, log_level.lower())
                    log_method(f"Exception in {func.__name__}: {str(e)}\n{tb_str}")
                    
                    # Notify admin if requested (for sync functions, we can't use async notifier)
                    if notify_admin and admin_notifier:
                        try:
                            logger.warning("Admin notification requested but not possible in sync function")
                        except Exception as notify_error:
                            logger.error(f"Failed to notify admin: {str(notify_error)}")
                    
                    return default_return
            
            # Return appropriate wrapper based on whether the function is async or not
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper
        
        # Handle case where decorator is used with or without arguments
        if func is None:
            return decorator
        return decorator(func)
    
    @staticmethod
    def retry(
        max_retries: int = 3,
        retry_delay: float = 1.0,
        exceptions: Union[Type[Exception], tuple] = Exception,
        log_level: str = "WARNING"
    ):
        """
        Decorator to retry functions on failure.
        
        Args:
            max_retries: Maximum number of retries
            retry_delay: Delay between retries in seconds
            exceptions: Exception type(s) to catch
            log_level: Log level for retry attempts
        
        Returns:
            Decorated function
        """
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                retries = 0
                while retries < max_retries:
                    try:
                        return await func(*args, **kwargs)
                    except exceptions as e:
                        retries += 1
                        
                        # Log retry attempt
                        log_method = getattr(logger, log_level.lower())
                        log_method(f"Retry {retries}/{max_retries} for {func.__name__}: {str(e)}")
                        
                        if retries >= max_retries:
                            logger.error(f"Max retries ({max_retries}) reached for {func.__name__}")
                            raise
                        
                        # Wait before retrying
                        await asyncio.sleep(retry_delay)
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                retries = 0
                while retries < max_retries:
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:
                        retries += 1
                        
                        # Log retry attempt
                        log_method = getattr(logger, log_level.lower())
                        log_method(f"Retry {retries}/{max_retries} for {func.__name__}: {str(e)}")
                        
                        if retries >= max_retries:
                            logger.error(f"Max retries ({max_retries}) reached for {func.__name__}")
                            raise
                        
                        # Wait before retrying
                        time.sleep(retry_delay)
            
            # Return appropriate wrapper based on whether the function is async or not
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper
        
        return decorator

# Add missing imports
import asyncio
import time
