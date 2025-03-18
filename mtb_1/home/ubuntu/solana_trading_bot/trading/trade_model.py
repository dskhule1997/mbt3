"""
Trade model for Solana trading.
This module defines the data model for trades.
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Trade:
    """
    Data model for a trade.
    """
    symbol: str
    address: str
    amount: float
    initial_price: float
    current_price: float
    initial_value: float
    current_value: float
    profit_percentage: float
    buy_time: datetime
    target_multiplier: float = 2.0
    sell_percentage: float = 80.0
    status: str = "active"
    last_updated: datetime = None
    
    def __post_init__(self):
        """Initialize default values after initialization."""
        if self.last_updated is None:
            self.last_updated = datetime.now()
    
    def update_price(self, new_price: float):
        """
        Update the current price and related values.
        
        Args:
            new_price: New token price
        """
        self.current_price = new_price
        self.current_value = self.amount * new_price
        self.profit_percentage = ((self.current_value / self.initial_value) - 1) * 100
        self.last_updated = datetime.now()
    
    def is_target_reached(self) -> bool:
        """
        Check if the target profit has been reached.
        
        Returns:
            bool: True if target reached, False otherwise
        """
        target_percentage = (self.target_multiplier - 1) * 100
        return self.profit_percentage >= target_percentage
    
    def calculate_sell_amount(self) -> float:
        """
        Calculate the amount to sell based on sell percentage.
        
        Returns:
            float: Amount to sell
        """
        return self.amount * (self.sell_percentage / 100)
    
    def to_dict(self):
        """
        Convert trade to dictionary.
        
        Returns:
            dict: Dictionary representation of the trade
        """
        return {
            'symbol': self.symbol,
            'address': self.address,
            'amount': self.amount,
            'initial_price': self.initial_price,
            'current_price': self.current_price,
            'initial_value': self.initial_value,
            'current_value': self.current_value,
            'profit_percentage': self.profit_percentage,
            'buy_time': self.buy_time.isoformat() if self.buy_time else None,
            'target_multiplier': self.target_multiplier,
            'sell_percentage': self.sell_percentage,
            'status': self.status,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }
    
    @classmethod
    def from_dict(cls, data):
        """
        Create trade from dictionary.
        
        Args:
            data: Dictionary containing trade data
        
        Returns:
            Trade: Trade instance
        """
        if 'buy_time' in data and data['buy_time']:
            data['buy_time'] = datetime.fromisoformat(data['buy_time'])
        
        if 'last_updated' in data and data['last_updated']:
            data['last_updated'] = datetime.fromisoformat(data['last_updated'])
        
        return cls(**data)
