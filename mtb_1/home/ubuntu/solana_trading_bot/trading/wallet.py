"""
Wallet manager for Solana trading.
This module handles Solana wallet operations.
"""
import base58
from typing import Optional, Tuple
from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.rpc.api import Client
from loguru import logger

class SolanaWallet:
    """
    Manager for Solana wallet operations.
    Handles wallet initialization, balance checking, and key management.
    """
    
    def __init__(self, private_key: str, rpc_url: str):
        """
        Initialize the Solana wallet.
        
        Args:
            private_key: Solana wallet private key (base58 encoded)
            rpc_url: Solana RPC URL
        """
        self.private_key = private_key
        self.rpc_url = rpc_url
        self.client = Client(rpc_url)
        self.keypair = None
        self.public_key = None
        
        # Initialize wallet
        self._initialize_wallet()
        
        logger.info("Solana wallet initialized")
    
    def _initialize_wallet(self):
        """Initialize the wallet from private key."""
        try:
            # Decode private key
            decoded_key = base58.b58decode(self.private_key)
            
            # Create keypair
            self.keypair = Keypair.from_secret_key(decoded_key)
            self.public_key = self.keypair.public_key
            
            logger.info(f"Wallet initialized with public key: {self.public_key}")
        except Exception as e:
            logger.error(f"Error initializing wallet: {str(e)}")
            raise
    
    async def get_sol_balance(self) -> float:
        """
        Get SOL balance for the wallet.
        
        Returns:
            float: SOL balance
        """
        try:
            response = self.client.get_balance(self.public_key)
            balance = response['result']['value'] / 1_000_000_000  # Convert lamports to SOL
            logger.debug(f"SOL balance: {balance}")
            return balance
        except Exception as e:
            logger.error(f"Error getting SOL balance: {str(e)}")
            return 0.0
    
    async def get_token_balance(self, token_address: str) -> Tuple[float, int]:
        """
        Get token balance for the wallet.
        
        Args:
            token_address: Token mint address
        
        Returns:
            Tuple[float, int]: Token balance and decimals
        """
        try:
            # Get token account
            token_pubkey = PublicKey(token_address)
            token_accounts = self.client.get_token_accounts_by_owner(
                self.public_key,
                {'mint': str(token_pubkey)}
            )
            
            # If no token account found, return 0
            if not token_accounts['result']['value']:
                logger.debug(f"No token account found for {token_address}")
                return 0.0, 0
            
            # Get balance from the first account
            account_data = token_accounts['result']['value'][0]['account']['data']
            token_balance = account_data['parsed']['info']['tokenAmount']
            
            # Extract balance and decimals
            amount = float(token_balance['amount']) / (10 ** token_balance['decimals'])
            decimals = token_balance['decimals']
            
            logger.debug(f"Token balance for {token_address}: {amount} (decimals: {decimals})")
            return amount, decimals
        
        except Exception as e:
            logger.error(f"Error getting token balance for {token_address}: {str(e)}")
            return 0.0, 0
    
    def get_public_key_str(self) -> str:
        """
        Get public key as string.
        
        Returns:
            str: Public key string
        """
        return str(self.public_key) if self.public_key else ""
