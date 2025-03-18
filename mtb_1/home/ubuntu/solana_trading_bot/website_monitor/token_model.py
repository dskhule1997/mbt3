"""
Token model for website monitoring.
This module defines the data model for tokens detected from websites.
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Token:
    """
    Data model for a token detected from a website.
    """
    symbol: str
    address: Optional[str] = None
    price: Optional[float] = None
    price_change_24h: Optional[float] = None
    volume_24h: Optional[float] = None
    market_cap: Optional[float] = None
    source: str = "Unknown"
    detected_at: datetime = None
    
    def __post_init__(self):
        """Initialize default values after initialization."""
        if self.detected_at is None:
            self.detected_at = datetime.now()
    
    def to_dict(self):
        """
        Convert token to dictionary.
        
        Returns:
            dict: Dictionary representation of the token
        """
        return {
            'symbol': self.symbol,
            'address': self.address,
            'price': self.price,
            'price_change_24h': self.price_change_24h,
            'volume_24h': self.volume_24h,
            'market_cap': self.market_cap,
            'source': self.source,
            'detected_at': self.detected_at.isoformat() if self.detected_at else None
        }
    
    @classmethod
    def from_dict(cls, data):
        """
        Create token from dictionary.
        
        Args:
            data: Dictionary containing token data
        
        Returns:
            Token: Token instance
        """
        if 'detected_at' in data and data['detected_at']:
            data['detected_at'] = datetime.fromisoformat(data['detected_at'])
        
        return cls(**data)
    
    def __hash__(self):
        """
        Hash function for token.
        
        Returns:
            int: Hash value
        """
        return hash(self.symbol)
    
    def __eq__(self, other):
        """
        Equality function for token.
        
        Args:
            other: Other token to compare with
        
        Returns:
            bool: True if equal, False otherwise
        """
        if not isinstance(other, Token):
            return False
        
        return self.symbol == other.symbol
