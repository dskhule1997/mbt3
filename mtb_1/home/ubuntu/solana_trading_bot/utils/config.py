"""
Configuration utility for the Solana Trading Bot.
Loads and provides access to all configuration parameters.
"""
import os
from typing import List

class Config:
    """Configuration class for the Solana Trading Bot."""
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        # Telegram User Client Configuration
        self.user_api_id = int(os.getenv('USER_API_ID'))
        self.user_api_hash = os.getenv('USER_API_HASH')
        self.user_phone = os.getenv('USER_PHONE')
        
        # Telegram Bot Client Configuration
        self.bot_token = os.getenv('BOT_TOKEN')
        self.admin_id = int(os.getenv('ADMIN_ID'))
        
        # Telegram Groups to Monitor
        self.telegram_groups = os.getenv('TELEGRAM_GROUPS', '').split(',')
        
        # Solana Configuration
        self.solana_private_key = os.getenv('SOLANA_PRIVATE_KEY')
        self.solana_rpc_url = os.getenv('SOLANA_RPC_URL')
        
        # Trading Parameters
        self.auto_trade_enabled = os.getenv('AUTO_TRADE_ENABLED', 'false').lower() == 'true'
        self.buy_amount_sol = float(os.getenv('BUY_AMOUNT_SOL', '0.1'))
        self.target_multiplier = float(os.getenv('TARGET_MULTIPLIER', '2.0'))
        self.sell_percentage = float(os.getenv('SELL_PERCENTAGE', '80'))
        
        # Website Monitoring
        self.jup_trenches_url = os.getenv('JUP_TRENCHES_URL', 'https://jup.ag/trenches?tab=trending')
        self.monitoring_interval = int(os.getenv('MONITORING_INTERVAL', '60'))
        
        # Logging
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
    
    def validate(self) -> bool:
        """
        Validate that all required configuration parameters are set.
        
        Returns:
            bool: True if all required parameters are set, False otherwise.
        """
        required_params = [
            self.user_api_id,
            self.user_api_hash,
            self.user_phone,
            self.bot_token,
            self.admin_id,
            self.solana_private_key,
            self.solana_rpc_url
        ]
        
        return all(param is not None and param != '' for param in required_params)
