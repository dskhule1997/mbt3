"""
Jupiter API client for Solana trading.
This module handles interactions with Jupiter Aggregator for token swaps.
"""
import json
import aiohttp
from typing import Dict, Optional, Tuple
from loguru import logger

class JupiterClient:
    """
    Client for Jupiter Aggregator API.
    Handles token swaps and price quotes.
    """
    
    def __init__(self):
        """Initialize the Jupiter client."""
        self.base_url = "https://quote-api.jup.ag/v6"
        self.wrapped_sol = "So11111111111111111111111111111111111111112"
        logger.info("Jupiter client initialized")
    
    async def get_quote(
        self,
        input_mint: str,
        output_mint: str,
        amount: float,
        slippage_bps: int = 50
    ) -> Optional[Dict]:
        """
        Get a swap quote from Jupiter.
        
        Args:
            input_mint: Input token address (or "SOL")
            output_mint: Output token address (or "SOL")
            amount: Amount to swap (in input token units)
            slippage_bps: Slippage tolerance in basis points (1 bps = 0.01%)
        
        Returns:
            Optional[Dict]: Swap quote or None if failed
        """
        try:
            # Convert SOL to wrapped SOL if needed
            if input_mint.upper() == "SOL":
                input_mint = self.wrapped_sol
            
            if output_mint.upper() == "SOL":
                output_mint = self.wrapped_sol
            
            # Convert amount to integer (Jupiter expects amounts in lamports/smallest unit)
            # This is a simplification - in a real implementation, we would need to
            # get the token's decimals and convert accordingly
            amount_in_lamports = int(amount * 1_000_000_000)  # Assuming 9 decimals like SOL
            
            # Build request URL
            url = f"{self.base_url}/quote"
            params = {
                "inputMint": input_mint,
                "outputMint": output_mint,
                "amount": str(amount_in_lamports),
                "slippageBps": slippage_bps
            }
            
            logger.debug(f"Getting quote: {params}")
            
            # Make request
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Error getting quote: {response.status} - {error_text}")
                        return None
                    
                    quote = await response.json()
                    logger.debug(f"Got quote: {quote}")
                    return quote
        
        except Exception as e:
            logger.error(f"Error getting swap quote: {str(e)}")
            return None
    
    async def get_swap_transaction(
        self,
        quote: Dict,
        user_public_key: str
    ) -> Optional[str]:
        """
        Get a swap transaction from Jupiter.
        
        Args:
            quote: Quote from get_quote
            user_public_key: User's public key
        
        Returns:
            Optional[str]: Base64 encoded transaction or None if failed
        """
        try:
            # Build request URL and data
            url = f"{self.base_url}/swap"
            data = {
                "quoteResponse": quote,
                "userPublicKey": user_public_key,
                "wrapUnwrapSOL": True
            }
            
            logger.debug(f"Getting swap transaction: {data}")
            
            # Make request
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Error getting swap transaction: {response.status} - {error_text}")
                        return None
                    
                    result = await response.json()
                    logger.debug("Got swap transaction")
                    return result.get('swapTransaction')
        
        except Exception as e:
            logger.error(f"Error getting swap transaction: {str(e)}")
            return None
    
    async def get_price(self, token_address: str) -> Optional[float]:
        """
        Get token price in SOL.
        
        Args:
            token_address: Token address
        
        Returns:
            Optional[float]: Token price in SOL or None if failed
        """
        try:
            # Use a small amount to get a quote
            quote = await self.get_quote(
                token_address,
                "SOL",
                1.0  # 1 token unit
            )
            
            if not quote:
                return None
            
            # Extract price from quote
            in_amount = float(quote['inAmount']) / 1_000_000_000  # Convert from lamports
            out_amount = float(quote['outAmount']) / 1_000_000_000  # Convert from lamports
            
            # Price in SOL per token
            price = out_amount / in_amount
            
            logger.debug(f"Price for {token_address}: {price} SOL")
            return price
        
        except Exception as e:
            logger.error(f"Error getting token price: {str(e)}")
            return None
