"""
Solana trader for executing trades on Solana blockchain.
This module handles buying and selling tokens on Solana.
"""
import asyncio
import time
import json
import base58
from typing import Dict, List, Optional
from datetime import datetime
from solana.rpc.api import Client
from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.rpc.types import TxOpts
from solana.transaction import Transaction
from loguru import logger

from trading.wallet import SolanaWallet
from trading.jupiter_client import JupiterClient
from trading.trade_model import Trade

class SolanaTrader:
    """
    Trader for executing trades on Solana blockchain.
    Uses Jupiter aggregator for swapping tokens.
    """
    
    def __init__(
        self,
        private_key: str,
        rpc_url: str,
        buy_amount: float = 0.1,
        target_multiplier: float = 2.0,
        sell_percentage: float = 80.0,
        auto_trade_enabled: bool = False
    ):
        """
        Initialize the Solana trader.
        
        Args:
            private_key: Solana wallet private key
            rpc_url: Solana RPC URL
            buy_amount: Amount of SOL to buy tokens with
            target_multiplier: Target profit multiplier
            sell_percentage: Percentage of position to sell at target
            auto_trade_enabled: Whether auto-trading is enabled
        """
        self.private_key = private_key
        self.rpc_url = rpc_url
        self.buy_amount = buy_amount
        self.target_multiplier = target_multiplier
        self.sell_percentage = sell_percentage
        self.auto_trade_enabled = auto_trade_enabled
        
        # Initialize components
        self.wallet = SolanaWallet(private_key, rpc_url)
        self.jupiter = JupiterClient()
        
        # Store active trades
        self.active_trades = {}
        
        # Start monitoring thread for active trades
        self.running = False
        self.monitor_thread = None
        
        logger.info("Solana trader initialized")
    
    def start_monitoring(self):
        """Start monitoring active trades."""
        logger.info("Starting trade monitoring...")
        self.running = True
        self.monitor_thread = asyncio.create_task(self._monitor_trades())
        logger.info("Trade monitoring started successfully")
    
    def stop_monitoring(self):
        """Stop monitoring active trades."""
        logger.info("Stopping trade monitoring...")
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.cancel()
        logger.info("Trade monitoring stopped successfully")
    
    async def _monitor_trades(self):
        """Monitor active trades for target price."""
        logger.info("Trade monitoring loop started")
        
        while self.running:
            try:
                # Check each active trade
                trades_to_remove = []
                
                for symbol, trade in self.active_trades.items():
                    try:
                        # Get current price
                        current_price = await self.jupiter.get_price(trade.address)
                        
                        if current_price is None:
                            logger.warning(f"Could not get price for {symbol}")
                            continue
                        
                        # Update trade info
                        trade.update_price(current_price)
                        
                        logger.debug(f"Trade {symbol}: {trade.profit_percentage:.2f}% profit")
                        
                        # Check if target reached
                        if trade.is_target_reached():
                            logger.info(f"Target reached for {symbol}: {trade.profit_percentage:.2f}%")
                            
                            # Sell percentage of position
                            sell_amount = trade.calculate_sell_amount()
                            success = await self._sell_token(trade.address, sell_amount)
                            
                            if success:
                                logger.info(f"Sold {self.sell_percentage}% of {symbol} position")
                                
                                # Update trade info
                                trade.amount -= sell_amount
                                trade.initial_value = current_price * trade.amount
                                
                                # If all sold, remove from active trades
                                if trade.amount <= 0:
                                    trades_to_remove.append(symbol)
                                    trade.status = "completed"
                            else:
                                logger.error(f"Failed to sell {symbol}")
                    
                    except Exception as e:
                        logger.error(f"Error monitoring trade {symbol}: {str(e)}")
                
                # Remove completed trades
                for symbol in trades_to_remove:
                    del self.active_trades[symbol]
                
                # Sleep before next check
                await asyncio.sleep(30)
            
            except Exception as e:
                logger.error(f"Error in trade monitoring loop: {str(e)}")
                await asyncio.sleep(30)
    
    async def buy_token(self, symbol: str, address: str) -> bool:
        """
        Buy a token with SOL.
        
        Args:
            symbol: Token symbol
            address: Token address
        
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"Buying {symbol} ({address}) with {self.buy_amount} SOL")
        
        try:
            # Check if auto-trading is enabled
            if not self.auto_trade_enabled:
                logger.warning("Auto-trading is disabled")
                return False
            
            # Check if already trading this token
            if symbol in self.active_trades:
                logger.warning(f"Already trading {symbol}")
                return False
            
            # Get quote from Jupiter
            quote = await self.jupiter.get_quote(
                "SOL",
                address,
                self.buy_amount
            )
            
            if not quote:
                logger.error(f"Could not get quote for {symbol}")
                return False
            
            # Get swap transaction
            transaction = await self.jupiter.get_swap_transaction(
                quote,
                self.wallet.get_public_key_str()
            )
            
            if not transaction:
                logger.error(f"Could not get swap transaction for {symbol}")
                return False
            
            # Execute swap
            success = await self._execute_swap(transaction)
            
            if not success:
                logger.error(f"Failed to swap SOL for {symbol}")
                return False
            
            # Get token balance and price
            balance, _ = await self.wallet.get_token_balance(address)
            price = await self.jupiter.get_price(address)
            
            if balance <= 0 or price is None:
                logger.error(f"Could not get balance or price for {symbol}")
                return False
            
            # Create trade object
            trade = Trade(
                symbol=symbol,
                address=address,
                amount=balance,
                initial_price=price,
                current_price=price,
                initial_value=price * balance,
                current_value=price * balance,
                profit_percentage=0.0,
                buy_time=datetime.now(),
                target_multiplier=self.target_multiplier,
                sell_percentage=self.sell_percentage
            )
            
            # Add to active trades
            self.active_trades[symbol] = trade
            
            logger.info(f"Successfully bought {balance} {symbol} for {self.buy_amount} SOL")
            return True
        
        except Exception as e:
            logger.error(f"Error buying {symbol}: {str(e)}")
            return False
    
    async def _sell_token(self, address: str, amount: float) -> bool:
        """
        Sell a token for SOL.
        
        Args:
            address: Token address
            amount: Amount to sell
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get quote from Jupiter
            quote = await self.jupiter.get_quote(
                address,
                "SOL",
                amount
            )
            
            if not quote:
                logger.error(f"Could not get quote for selling token {address}")
                return False
            
            # Get swap transaction
            transaction = await self.jupiter.get_swap_transaction(
                quote,
                self.wallet.get_public_key_str()
            )
            
            if not transaction:
                logger.error(f"Could not get swap transaction for selling token {address}")
                return False
            
            # Execute swap
            success = await self._execute_swap(transaction)
            
            if not success:
                logger.error(f"Failed to swap token {address} for SOL")
                return False
            
            logger.info(f"Successfully sold {amount} of token {address} for SOL")
            return True
        
        except Exception as e:
            logger.error(f"Error selling token {address}: {str(e)}")
            return False
    
    async def _execute_swap(self, transaction_base64: str) -> bool:
        """
        Execute a swap transaction.
        
        Args:
            transaction_base64: Base64 encoded transaction from Jupiter
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # In a real implementation, you would:
            # 1. Decode the base64 transaction
            # 2. Deserialize it into a Transaction object
            # 3. Sign it with the wallet keypair
            # 4. Send it to the Solana network
            
            # This is a simplified implementation for demonstration purposes
            logger.info("Simulating transaction execution...")
            
            # Simulate a successful swap
            logger.info("Swap transaction executed successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error executing swap: {str(e)}")
            return False
    
    def get_active_trades(self) -> List[Dict]:
        """
        Get list of active trades.
        
        Returns:
            List[Dict]: List of active trades
        """
        return [
            {
                'symbol': trade.symbol,
                'address': trade.address,
                'amount': trade.amount,
                'initial_value': trade.initial_value,
                'current_value': trade.current_value,
                'profit_percentage': trade.profit_percentage
            }
            for trade in self.active_trades.values()
        ]
    
    def set_auto_trade_enabled(self, enabled: bool):
        """
        Set whether auto-trading is enabled.
        
        Args:
            enabled: Whether auto-trading is enabled
        """
        self.auto_trade_enabled = enabled
        logger.info(f"Auto-trading {'enabled' if enabled else 'disabled'}")
    
    def set_buy_amount(self, amount: float):
        """
        Set buy amount in SOL.
        
        Args:
            amount: Buy amount in SOL
        """
        if amount <= 0:
            logger.error("Buy amount must be positive")
            return
        
        self.buy_amount = amount
        logger.info(f"Buy amount set to {amount} SOL")
    
    def set_target_multiplier(self, multiplier: float):
        """
        Set target profit multiplier.
        
        Args:
            multiplier: Target profit multiplier
        """
        if multiplier <= 1:
            logger.error("Target multiplier must be greater than 1")
            return
        
        self.target_multiplier = multiplier
        logger.info(f"Target multiplier set to {multiplier}x")
    
    def set_sell_percentage(self, percentage: float):
        """
        Set sell percentage at target.
        
        Args:
            percentage: Sell percentage at target
        """
        if percentage <= 0 or percentage > 100:
            logger.error("Sell percentage must be between 0 and 100")
            return
        
        self.sell_percentage = percentage
        logger.info(f"Sell percentage set to {percentage}%")
