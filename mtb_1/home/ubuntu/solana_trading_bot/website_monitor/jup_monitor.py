"""
JupTrenches monitor for website monitoring.
This module handles monitoring the jup.ag/trenches website for new tokens.
"""
import os
import time
from typing import Dict, List, Optional
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from loguru import logger

from website_monitor.base_monitor import BaseWebsiteMonitor
from website_monitor.token_model import Token

class JupTrenchesMonitor(BaseWebsiteMonitor):
    """
    Monitor for jup.ag/trenches website.
    Uses Selenium to monitor the website for new tokens.
    """
    
    def __init__(self, url: str, interval: int = 60):
        """
        Initialize the JupTrenches monitor.
        
        Args:
            url: URL of the jup.ag/trenches website
            interval: Monitoring interval in seconds
        """
        super().__init__(url, interval)
        
        # Selenium WebDriver
        self.driver = None
        
        # Configure Selenium options
        self.options = Options()
        self.options.add_argument("--headless")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--disable-gpu")
        self.options.add_argument("--window-size=1920,1080")
        
        # Create logs directory if it doesn't exist
        os.makedirs("logs", exist_ok=True)
        
        logger.info("JupTrenches monitor initialized")
    
    def _initialize(self):
        """Initialize the Selenium WebDriver."""
        try:
            logger.info("Initializing WebDriver...")
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=self.options)
            logger.info("WebDriver initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing WebDriver: {str(e)}")
            raise
    
    def _cleanup(self):
        """Clean up the Selenium WebDriver."""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("WebDriver closed")
            except Exception as e:
                logger.error(f"Error closing WebDriver: {str(e)}")
    
    def _extract_tokens(self) -> List[Token]:
        """
        Extract token information from the website.
        
        Returns:
            List of Token objects
        """
        tokens = []
        
        try:
            # Navigate to the website
            logger.info(f"Navigating to {self.url}")
            self.driver.get(self.url)
            
            # Wait for the page to load
            logger.info("Waiting for page to load...")
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table"))
            )
            
            # Wait for the trending table to load
            logger.info("Waiting for trending table to load...")
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr"))
            )
            
            # Take screenshot for debugging
            try:
                screenshot_path = "logs/jup_trenches.png"
                self.driver.save_screenshot(screenshot_path)
                logger.debug(f"Screenshot saved to {screenshot_path}")
            except Exception as e:
                logger.warning(f"Failed to save screenshot: {str(e)}")
            
            # Find all rows in the trending table
            rows = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
            logger.info(f"Found {len(rows)} rows in the trending table")
            
            for row in rows:
                try:
                    # Extract token information from the row
                    cells = row.find_elements(By.TAG_NAME, "td")
                    
                    if len(cells) < 3:
                        logger.warning(f"Row has less than 3 cells, skipping")
                        continue
                    
                    # Extract symbol
                    try:
                        symbol_element = cells[0].find_element(By.CSS_SELECTOR, "div[data-testid='token-symbol']")
                        symbol = symbol_element.text.strip()
                    except Exception as e:
                        logger.warning(f"Failed to extract symbol: {str(e)}")
                        # Try alternative method
                        try:
                            symbol = cells[0].text.strip().split('\n')[0]
                        except:
                            logger.error("Could not extract symbol using alternative method")
                            continue
                    
                    # Extract address
                    address = None
                    try:
                        # Try to find the address in the data attribute
                        address_element = cells[0].find_element(By.CSS_SELECTOR, "div[data-mint]")
                        address = address_element.get_attribute("data-mint")
                    except:
                        # If not found, try to extract from the link
                        try:
                            link_element = cells[0].find_element(By.TAG_NAME, "a")
                            href = link_element.get_attribute("href")
                            if "=" in href:
                                address = href.split("=")[-1]
                        except:
                            logger.warning(f"Could not extract address for {symbol}")
                    
                    # Extract price
                    price = None
                    try:
                        price_element = cells[1].find_element(By.CSS_SELECTOR, "div")
                        price_text = price_element.text.strip()
                        # Remove $ and convert to float
                        if price_text.startswith("$"):
                            price = float(price_text[1:].replace(",", ""))
                    except Exception as e:
                        logger.warning(f"Failed to extract price: {str(e)}")
                    
                    # Extract price change
                    price_change_24h = None
                    try:
                        if len(cells) > 2:
                            change_element = cells[2].find_element(By.CSS_SELECTOR, "div")
                            change_text = change_element.text.strip()
                            # Remove % and convert to float
                            if "%" in change_text:
                                change_text = change_text.replace("%", "")
                                price_change_24h = float(change_text)
                    except Exception as e:
                        logger.warning(f"Failed to extract price change: {str(e)}")
                    
                    # Extract volume
                    volume_24h = None
                    try:
                        if len(cells) > 3:
                            volume_element = cells[3].find_element(By.CSS_SELECTOR, "div")
                            volume_text = volume_element.text.strip()
                            # Remove $ and convert to float
                            if volume_text.startswith("$"):
                                volume_text = volume_text[1:].replace(",", "")
                                # Handle K, M, B suffixes
                                if "K" in volume_text:
                                    volume_24h = float(volume_text.replace("K", "")) * 1000
                                elif "M" in volume_text:
                                    volume_24h = float(volume_text.replace("M", "")) * 1000000
                                elif "B" in volume_text:
                                    volume_24h = float(volume_text.replace("B", "")) * 1000000000
                                else:
                                    volume_24h = float(volume_text)
                    except Exception as e:
                        logger.warning(f"Failed to extract volume: {str(e)}")
                    
                    # Create token object
                    token = Token(
                        symbol=symbol,
                        address=address,
                        price=price,
                        price_change_24h=price_change_24h,
                        volume_24h=volume_24h,
                        source="jup.ag/trenches"
                    )
                    
                    tokens.append(token)
                    logger.debug(f"Extracted token: {symbol}")
                
                except Exception as e:
                    logger.error(f"Error extracting token from row: {str(e)}")
            
            logger.info(f"Extracted {len(tokens)} tokens from the website")
        
        except Exception as e:
            logger.error(f"Error extracting tokens: {str(e)}")
            # Take screenshot for debugging
            try:
                screenshot_path = "logs/website_error.png"
                self.driver.save_screenshot(screenshot_path)
                logger.info(f"Error screenshot saved to {screenshot_path}")
            except:
                pass
        
        return tokens
