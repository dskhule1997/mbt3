"""
Selenium error handler for Solana Trading Bot.
This module provides specific error handling for Selenium WebDriver errors.
"""
import time
import asyncio
from functools import wraps
from selenium.common.exceptions import (
    WebDriverException,
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
    ElementNotVisibleException,
    ElementClickInterceptedException
)
from loguru import logger

from utils.error_handler import ErrorHandler

class SeleniumErrorHandler:
    """
    Selenium error handler.
    Provides specific error handling for Selenium WebDriver errors.
    """
    
    # Common Selenium errors and their retry strategies
    TIMEOUT_ERRORS = (
        TimeoutException,
    )
    
    ELEMENT_ERRORS = (
        NoSuchElementException,
        StaleElementReferenceException,
        ElementNotVisibleException,
        ElementClickInterceptedException
    )
    
    WEBDRIVER_ERRORS = (
        WebDriverException,
    )
    
    @staticmethod
    def handle_selenium_errors(func=None, default_return=None, log_level="ERROR"):
        """
        Decorator to handle Selenium errors.
        
        Args:
            func: Function to decorate
            default_return: Default return value if error occurs
            log_level: Log level for errors
        
        Returns:
            Decorated function
        """
        return ErrorHandler.handle_exceptions(
            func=func,
            exceptions=(WebDriverException,),
            default_return=default_return,
            log_level=log_level
        )
    
    @staticmethod
    def retry_selenium_operation(max_retries=3, retry_delay=1.0):
        """
        Decorator to retry Selenium operations on failure.
        
        Args:
            max_retries: Maximum number of retries
            retry_delay: Delay between retries in seconds
        
        Returns:
            Decorated function
        """
        return ErrorHandler.retry(
            max_retries=max_retries,
            retry_delay=retry_delay,
            exceptions=(
                TimeoutException,
                NoSuchElementException,
                StaleElementReferenceException,
                ElementNotVisibleException,
                ElementClickInterceptedException
            ),
            log_level="WARNING"
        )
    
    @staticmethod
    def wait_for_element(timeout=10, poll_frequency=0.5):
        """
        Decorator to wait for an element to be available.
        
        Args:
            timeout: Maximum time to wait in seconds
            poll_frequency: Time between polls in seconds
        
        Returns:
            Decorated function
        """
        def decorator(func):
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                last_exception = None
                
                while time.time() - start_time < timeout:
                    try:
                        return func(*args, **kwargs)
                    except (NoSuchElementException, StaleElementReferenceException) as e:
                        last_exception = e
                        time.sleep(poll_frequency)
                
                # If we get here, we timed out
                logger.warning(f"Timed out waiting for element in {func.__name__}: {str(last_exception)}")
                raise TimeoutException(f"Timed out waiting for element: {str(last_exception)}")
            
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                last_exception = None
                
                while time.time() - start_time < timeout:
                    try:
                        return await func(*args, **kwargs)
                    except (NoSuchElementException, StaleElementReferenceException) as e:
                        last_exception = e
                        await asyncio.sleep(poll_frequency)
                
                # If we get here, we timed out
                logger.warning(f"Timed out waiting for element in {func.__name__}: {str(last_exception)}")
                raise TimeoutException(f"Timed out waiting for element: {str(last_exception)}")
            
            # Return appropriate wrapper based on whether the function is async or not
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper
        
        return decorator
    
    @staticmethod
    def take_screenshot_on_error(driver, screenshot_dir="logs"):
        """
        Decorator to take a screenshot when an error occurs.
        
        Args:
            driver: Selenium WebDriver instance
            screenshot_dir: Directory to save screenshots
        
        Returns:
            Decorated function
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    # Take screenshot
                    try:
                        import os
                        from datetime import datetime
                        
                        # Create directory if it doesn't exist
                        os.makedirs(screenshot_dir, exist_ok=True)
                        
                        # Generate filename with timestamp
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"{screenshot_dir}/error_{func.__name__}_{timestamp}.png"
                        
                        # Save screenshot
                        driver.save_screenshot(filename)
                        logger.info(f"Screenshot saved to {filename}")
                    
                    except Exception as screenshot_error:
                        logger.error(f"Failed to take screenshot: {str(screenshot_error)}")
                    
                    # Re-raise the original exception
                    raise
            
            return wrapper
        
        return decorator
