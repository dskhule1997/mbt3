"""
Bot client for Telegram integration.
This module handles command processing and notifications using a bot account.
"""
import asyncio
import os
import time
from typing import Dict, List, Optional, Callable
from telethon import TelegramClient, events, Button
from telethon.tl.types import User
from loguru import logger

from telegram.client_factory import TelegramClientFactory

class BotClient:
    """
    Bot client for Telegram integration.
    Uses a bot account to handle commands and send notifications.
    """
    
    def __init__(self, token: str, admin_id: int):
        """
        Initialize the bot client.
        
        Args:
            token: Bot token from BotFather
            admin_id: Telegram user ID of the admin
        """
        self.token = token
        self.admin_id = admin_id
        self.client = None
        self.session_string = None
        self.trader = None
        self.running = False
        
        # Session file path
        self.session_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "config",
            "bot_session.txt"
        )
        
        # Store detected tokens
        self.detected_tokens = {}
        
        logger.info("Bot client initialized")
    
    async def start(self):
        """Start the bot client and connect to Telegram."""
        logger.info("Starting bot client...")
        
        # Load session if exists
        self.session_string = TelegramClientFactory.load_session(self.session_file)
        
        # Create client
        self.client, self.session_string = await TelegramClientFactory.create_bot_client(
            token=self.token,
            session_string=self.session_string
        )
        
        # Save session
        TelegramClientFactory.save_session(self.session_string, self.session_file)
        
        # Setup command handlers
        self.client.add_event_handler(
            self._start_command,
            events.NewMessage(pattern='/start')
        )
        
        self.client.add_event_handler(
            self._help_command,
            events.NewMessage(pattern='/help')
        )
        
        self.client.add_event_handler(
            self._status_command,
            events.NewMessage(pattern='/status')
        )
        
        self.client.add_event_handler(
            self._settings_command,
            events.NewMessage(pattern='/settings')
        )
        
        self.client.add_event_handler(
            self._toggle_autotrade_command,
            events.NewMessage(pattern='/toggle_autotrade')
        )
        
        self.client.add_event_handler(
            self._set_buy_amount_command,
            events.NewMessage(pattern='/set_buy_amount')
        )
        
        self.client.add_event_handler(
            self._set_target_multiplier_command,
            events.NewMessage(pattern='/set_target_multiplier')
        )
        
        self.client.add_event_handler(
            self._set_sell_percentage_command,
            events.NewMessage(pattern='/set_sell_percentage')
        )
        
        # Setup callback query handler for buttons
        self.client.add_event_handler(
            self._button_callback,
            events.CallbackQuery()
        )
        
        logger.info("Bot client started successfully")
        
        # Get bot info for logging
        me = await self.client.get_me()
        logger.info(f"Bot logged in as: {me.first_name} (@{me.username})")
        
        # Send startup notification to admin
        try:
            await self.client.send_message(
                self.admin_id,
                "🤖 Solana Trading Bot is now online!"
            )
        except Exception as e:
            logger.error(f"Failed to send startup notification: {str(e)}")
    
    async def stop(self):
        """Stop the bot client and disconnect from Telegram."""
        logger.info("Stopping bot client...")
        await self.client.disconnect()
        logger.info("Bot client stopped successfully")
    
    async def run(self):
        """Run the bot client in a loop."""
        self.running = True
        logger.info("Bot client is now running")
        
        while self.running:
            await asyncio.sleep(1)
    
    def set_trader(self, trader):
        """
        Set the trader instance for executing trades.
        
        Args:
            trader: SolanaTrader instance
        """
        self.trader = trader
        logger.info("Trader set for bot client")
    
    async def send_token_notification(self, token_info: Dict):
        """
        Send notification about a detected token.
        
        Args:
            token_info: Dictionary containing token information
        """
        if not token_info.get('symbol'):
            logger.warning("Received token notification without symbol")
            return
        
        symbol = token_info['symbol']
        address = token_info.get('address', 'Unknown')
        source = token_info.get('source', 'Unknown')
        
        # Skip if we've already notified about this token recently
        if symbol in self.detected_tokens:
            logger.info(f"Token {symbol} already notified recently, skipping")
            return
        
        # Store token for deduplication
        self.detected_tokens[symbol] = {
            'address': address,
            'source': source,
            'timestamp': asyncio.get_event_loop().time()
        }
        
        # Clean up old tokens (older than 1 hour)
        current_time = asyncio.get_event_loop().time()
        self.detected_tokens = {
            k: v for k, v in self.detected_tokens.items()
            if current_time - v['timestamp'] < 3600
        }
        
        # Create notification message
        message = f"🚨 **New Token Detected** 🚨\n\n"
        message += f"**Symbol:** {symbol}\n"
        message += f"**Address:** {address}\n"
        message += f"**Source:** {source}\n\n"
        
        if token_info.get('price'):
            message += f"**Price:** ${token_info['price']}\n\n"
        
        if token_info.get('message'):
            # Truncate message if too long
            orig_message = token_info['message']
            if len(orig_message) > 200:
                orig_message = orig_message[:197] + "..."
            message += f"**Original Message:**\n{orig_message}\n\n"
        
        # Add buttons
        buttons = [
            [Button.inline("🚀 Auto-Trade", data=f"trade_{symbol}_{address}")],
            [Button.inline("🔍 View on Jupiter", data=f"view_{symbol}_{address}")]
        ]
        
        try:
            # Send notification to admin
            await self.client.send_message(
                self.admin_id,
                message,
                buttons=buttons
            )
            logger.info(f"Sent token notification for {symbol} to admin")
        except Exception as e:
            logger.error(f"Failed to send token notification: {str(e)}")
    
    async def _start_command(self, event):
        """Handle /start command."""
        user = await event.get_sender()
        
        # Only respond to admin
        if user.id != self.admin_id:
            return
        
        welcome_message = (
            "👋 **Welcome to Solana Trading Bot!**\n\n"
            "This bot monitors Telegram groups and jup.ag/trenches for new Solana tokens "
            "and can automatically trade them based on your settings.\n\n"
            "Use /help to see available commands."
        )
        
        await event.respond(welcome_message)
        logger.info(f"Sent welcome message to user {user.id}")
    
    async def _help_command(self, event):
        """Handle /help command."""
        user = await event.get_sender()
        
        # Only respond to admin
        if user.id != self.admin_id:
            return
        
        help_message = (
            "📚 **Available Commands:**\n\n"
            "/start - Start the bot\n"
            "/help - Show this help message\n"
            "/status - Show current bot status and active trades\n"
            "/settings - Show current settings\n"
            "/toggle_autotrade - Enable/disable auto-trading\n"
            "/set_buy_amount <amount> - Set buy amount in SOL\n"
            "/set_target_multiplier <multiplier> - Set target profit multiplier\n"
            "/set_sell_percentage <percentage> - Set sell percentage at target\n"
        )
        
        await event.respond(help_message)
        logger.info(f"Sent help message to user {user.id}")
    
    async def _status_command(self, event):
        """Handle /status command."""
        user = await event.get_sender()
        
        # Only respond to admin
        if user.id != self.admin_id:
            return
        
        if not self.trader:
            await event.respond("⚠️ Trader not initialized")
            return
        
        # Get status from trader
        auto_trade_status = "Enabled ✅" if self.trader.auto_trade_enabled else "Disabled ❌"
        active_trades = self.trader.get_active_trades()
        
        status_message = f"📊 **Bot Status**\n\n"
        status_message += f"**Auto-Trading:** {auto_trade_status}\n"
        status_message += f"**Buy Amount:** {self.trader.buy_amount} SOL\n"
        status_message += f"**Target Multiplier:** {self.trader.target_multiplier}x\n"
        status_message += f"**Sell Percentage:** {self.trader.sell_percentage}%\n\n"
        
        if active_trades:
            status_message += "**Active Trades:**\n"
            for trade in active_trades:
                status_message += f"- {trade['symbol']}: {trade['current_value']} SOL ({trade['profit_percentage']}%)\n"
        else:
            status_message += "**No active trades**\n"
        
        await event.respond(status_message)
        logger.info(f"Sent status message to user {user.id}")
    
    async def _settings_command(self, event):
        """Handle /settings command."""
        user = await event.get_sender()
        
        # Only respond to admin
        if user.id != self.admin_id:
            return
        
        if not self.trader:
            await event.respond("⚠️ Trader not initialized")
            return
        
        # Create settings message with buttons
        auto_trade_status = "Enabled ✅" if self.trader.auto_trade_enabled else "Disabled ❌"
        
        settings_message = f"⚙️ **Bot Settings**\n\n"
        settings_message += f"**Auto-Trading:** {auto_trade_status}\n"
        settings_message += f"**Buy Amount:** {self.trader.buy_amount} SOL\n"
        settings_message += f"**Target Multiplier:** {self.trader.target_multiplier}x\n"
        settings_message += f"**Sell Percentage:** {self.trader.sell_percentage}%\n"
        
        buttons = [
            [Button.inline("Toggle Auto-Trade", data="toggle_autotrade")],
            [
                Button.inline("Buy Amount", data="set_buy_amount"),
                Button.inline("Target Multiplier", data="set_target_multiplier")
            ],
            [Button.inline("Sell Percentage", data="set_sell_percentage")]
        ]
        
        await event.respond(settings_message, buttons=buttons)
        logger.info(f"Sent settings message to user {user.id}")
    
    async def _toggle_autotrade_command(self, event):
        """Handle /toggle_autotrade command."""
        user = await event.get_sender()
        
        # Only respond to admin
        if user.id != self.admin_id:
            return
        
        if not self.trader:
            await event.respond("⚠️ Trader not initialized")
            return
        
        # Toggle auto-trade
        self.trader.auto_trade_enabled = not self.trader.auto_trade_enabled
        status = "enabled" if self.trader.auto_trade_enabled else "disabled"
        
        await event.respond(f"🔄 Auto-trading {status}")
        logger.info(f"Auto-trading {status} by user {user.id}")
    
    async def _set_buy_amount_command(self, event):
        """Handle /set_buy_amount command."""
        user = await event.get_sender()
        
        # Only respond to admin
        if user.id != self.admin_id:
            return
        
        if not self.trader:
            await event.respond("⚠️ Trader not initialized")
            return
        
        # Get amount from message
        try:
            amount = float(event.message.text.split(' ')[1])
            if amount <= 0:
                raise ValueError("Amount must be positive")
            
            self.trader.buy_amount = amount
            await event.respond(f"💰 Buy amount set to {amount} SOL")
            logger.info(f"Buy amount set to {amount} SOL by user {user.id}")
        except (IndexError, ValueError) as e:
            await event.respond("⚠️ Invalid amount. Usage: /set_buy_amount <amount>")
            logger.error(f"Invalid buy amount: {str(e)}")
    
    async def _set_target_multiplier_command(self, event):
        """Handle /set_target_multiplier command."""
        user = await event.get_sender()
        
        # Only respond to admin
        if user.id != self.admin_id:
            return
        
        if not self.trader:
            await event.respond("⚠️ Trader not initialized")
            return
        
        # Get multiplier from message
        try:
            multiplier = float(event.message.text.split(' ')[1])
            if multiplier <= 1:
                raise ValueError("Multiplier must be greater than 1")
            
            self.trader.target_multiplier = multiplier
            await event.respond(f"🎯 Target multiplier set to {multiplier}x")
            logger.info(f"Target multiplier set to {multiplier}x by user {user.id}")
        except (IndexError, ValueError) as e:
            await event.respond("⚠️ Invalid multiplier. Usage: /set_target_multiplier <multiplier>")
            logger.error(f"Invalid target multiplier: {str(e)}")
    
    async def _set_sell_percentage_command(self, event):
        """Handle /set_sell_percentage command."""
        user = await event.get_sender()
        
        # Only respond to admin
        if user.id != self.admin_id:
            return
        
        if not self.trader:
            await event.respond("⚠️ Trader not initialized")
            return
        
        # Get percentage from message
        try:
            percentage = float(event.message.text.split(' ')[1])
            if percentage <= 0 or percentage > 100:
                raise ValueError("Percentage must be between 0 and 100")
            
            self.trader.sell_percentage = percentage
            await event.respond(f"📊 Sell percentage set to {percentage}%")
            logger.info(f"Sell percentage set to {percentage}% by user {user.id}")
        except (IndexError, ValueError) as e:
            await event.respond("⚠️ Invalid percentage. Usage: /set_sell_percentage <percentage>")
            logger.error(f"Invalid sell percentage: {str(e)}")
    
    async def _button_callback(self, event):
        """Handle button callbacks."""
        user = await event.get_sender()
        
        # Only respond to admin
        if user.id != self.admin_id:
            return
        
        data = event.data.decode('utf-8')
        logger.info(f"Button callback: {data}")
        
        if data == "toggle_autotrade":
            # Toggle auto-trade
            if not self.trader:
                await event.answer("⚠️ Trader not initialized")
                return
            
            self.trader.auto_trade_enabled = not self.trader.auto_trade_enabled
            status = "enabled" if self.trader.auto_trade_enabled else "disabled"
            
            await event.answer(f"Auto-trading {status}")
            logger.info(f"Auto-trading {status} by user {user.id}")
            
            # Update settings message
            await self._settings_command(event)
        
        elif data<response clipped><NOTE>To save on context only part of this file has been shown to you. You should retry this tool after you have searched inside the file with `grep -n` in order to find the line numbers of what you are looking for.</NOTE>