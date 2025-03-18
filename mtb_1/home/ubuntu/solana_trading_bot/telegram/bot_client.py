"""
Telegram bot client for Solana Trading Bot.
This module handles the bot client functionality.
"""
import asyncio
import re
from typing import Callable, Dict, List, Optional, Union
from telethon import TelegramClient, events, Button
from telethon.tl.types import User
from loguru import logger

from utils.telegram_error_handler import TelegramErrorHandler

class BotClient:
    """
    Telegram bot client for handling commands and sending notifications.
    Uses the Telethon library with a bot token.
    """
    
    def __init__(
        self,
        token: str,
        admin_id: int,
        user_client = None
    ):
        """
        Initialize the bot client.
        
        Args:
            token: Bot token from BotFather
            admin_id: Telegram user ID of the admin
            user_client: User client instance for group operations
        """
        self.token = token
        self.admin_id = admin_id
        self.user_client = user_client
        self.client = TelegramClient('bot_session', api_id=123456, api_hash='dummy')
        self.client.parse_mode = 'markdown'
        
        # Set bot token
        self.client.session.set_dc(2, '149.154.167.40', 443)
        self.client._bot_token = token
        
        # Command handlers
        self.command_handlers = {}
        self.button_callback = None
        
        # Trading component
        self.trader = None
        
        # Register default handlers
        self._register_default_handlers()
        
        logger.info("Bot client initialized")
    
    async def start(self):
        """Start the bot client."""
        await self.client.start(bot_token=self.token)
        me = await self.client.get_me()
        logger.info(f"Bot started as @{me.username}")
    
    async def stop(self):
        """Stop the bot client."""
        await self.client.disconnect()
        logger.info("Bot client stopped")
    
    async def run(self):
        """Run the bot client indefinitely."""
        logger.info("Bot client running...")
        while True:
            await asyncio.sleep(1)
    
    def set_trader(self, trader):
        """
        Set the trader component.
        
        Args:
            trader: Trader component
        """
        self.trader = trader
        logger.info("Trader component set")
    
    def register_command_handler(self, command: str, handler: Callable):
        """
        Register a command handler.
        
        Args:
            command: Command name without slash
            handler: Handler function
        """
        self.command_handlers[command] = handler
        logger.info(f"Registered handler for /{command}")
    
    def register_button_callback(self, callback: Callable):
        """
        Register a button callback handler.
        
        Args:
            callback: Callback function
        """
        self.button_callback = callback
        logger.info("Registered button callback handler")
    
    def _register_default_handlers(self):
        """Register default command handlers."""
        # Register command handler
        @self.client.on(events.NewMessage(pattern=r'/[a-zA-Z0-9_]+'))
        async def handle_command(event):
            """Handle bot commands."""
            # Extract command
            command = event.raw_text.split()[0][1:]
            
            # Check if handler exists
            if command in self.command_handlers:
                try:
                    await self.command_handlers[command](event)
                except Exception as e:
                    logger.error(f"Error handling command /{command}: {str(e)}")
                    await event.respond(f"❌ Error executing command: {str(e)}")
            else:
                await event.respond(f"❌ Unknown command: /{command}")
        
        # Register button callback handler
        @self.client.on(events.CallbackQuery())
        async def handle_button(event):
            """Handle button callbacks."""
            if self.button_callback:
                try:
                    await self.button_callback(event)
                except Exception as e:
                    logger.error(f"Error handling button callback: {str(e)}")
                    await event.answer(f"Error: {str(e)}", alert=True)
            else:
                await event.answer("No button handler registered", alert=True)
    
    @TelegramErrorHandler.handle_telegram_errors
    async def send_message(
        self,
        user_id: int,
        text: str,
        buttons: Optional[List] = None,
        link_preview: bool = False
    ):
        """
        Send a message to a user.
        
        Args:
            user_id: Telegram user ID
            text: Message text
            buttons: Optional buttons
            link_preview: Whether to show link preview
        
        Returns:
            Sent message
        """
        return await self.client.send_message(
            user_id,
            text,
            buttons=buttons,
            link_preview=link_preview
        )
    
    @TelegramErrorHandler.handle_telegram_errors
    async def send_token_notification(self, token_data: Dict):
        """
        Send a notification about a detected token.
        
        Args:
            token_data: Token data
        """
        symbol = token_data.get("symbol", "Unknown")
        address = token_data.get("address")
        price = token_data.get("price")
        source = token_data.get("source", "Unknown")
        
        if not address:
            logger.warning(f"No address for token {symbol}, skipping notification")
            return
        
        # Create notification message
        message = (
            f"🔔 **New Token Detected!**\n\n"
            f"🔹 Symbol: **{symbol}**\n"
            f"🔹 Address: `{address}`\n"
        )
        
        if price:
            message += f"🔹 Price: **{price}**\n"
        
        message += f"🔹 Source: **{source}**\n\n"
        
        # Add auto-trade status
        if self.trader and self.trader.auto_trade_enabled:
            message += "🤖 Auto-trading is enabled. Trading this token automatically."
            
            # Auto-trade the token
            asyncio.create_task(self.trader.buy_token(symbol, address))
        else:
            message += "🤖 Auto-trading is disabled. Click the button below to trade this token."
        
        # Add buttons
        buttons = [
            [Button.inline(f"Trade {symbol}", data=f"trade_{symbol}_{address}")]
        ]
        
        # Send notification to admin
        await self.send_message(
            self.admin_id,
            message,
            buttons=buttons
        )
        
        logger.info(f"Sent notification for token {symbol}")
    
    async def handle_start(self, event):
        """
        Handle /start command.
        
        Args:
            event: Telegram event
        """
        welcome_message = (
            "🤖 **Welcome to Solana Trading Bot!**\n\n"
            "This bot monitors Telegram groups and jup.ag/trenches for new Solana tokens "
            "and can automatically trade them.\n\n"
            "**Commands:**\n"
            "/help - Show available commands\n"
            "/status - Show bot status\n"
            "/settings - Show current settings\n"
            "/trades - Show active trades\n"
            "/enable - Enable auto-trading\n"
            "/disable - Disable auto-trading\n"
            "/setbuy <amount> - Set buy amount in SOL\n"
            "/settarget <multiplier> - Set target profit multiplier\n"
            "/setsell <percentage> - Set sell percentage at target"
        )
        
        await self.send_message(
            event.chat_id,
            welcome_message
        )
    
    async def handle_help(self, event):
        """
        Handle /help command.
        
        Args:
            event: Telegram event
        """
        help_message = (
            "📚 **Available Commands:**\n\n"
            "/status - Show bot status\n"
            "/settings - Show current settings\n"
            "/trades - Show active trades\n"
            "/enable - Enable auto-trading\n"
            "/disable - Disable auto-trading\n"
            "/setbuy <amount> - Set buy amount in SOL\n"
            "/settarget <multiplier> - Set target profit multiplier\n"
            "/setsell <percentage> - Set sell percentage at target"
        )
        
        await self.send_message(
            event.chat_id,
            help_message
        )
    
    async def handle_status(self, event):
        """
        Handle /status command.
        
        Args:
            event: Telegram event
        """
        if not self.trader:
            await self.send_message(
                event.chat_id,
                "❌ Trader component not initialized"
            )
            return
        
        # Get wallet balance
        sol_balance = await self.trader.wallet.get_sol_balance()
        
        # Get active trades count
        active_trades = len(self.trader.active_trades)
        
        # Get auto-trade status
        auto_trade_status = "Enabled" if self.trader.auto_trade_enabled else "Disabled"
        
        # Get monitored groups count
        groups_count = 0
        if self.user_client:
            groups = await self.user_client.get_dialogs()
            groups_count = sum(1 for g in groups if hasattr(g.entity, 'title') and g.entity.title)
        
        status_message = (
            "📊 **Bot Status:**\n\n"
            f"🔹 Auto-Trading: **{auto_trade_status}**\n"
            f"🔹 SOL Balance: **{sol_balance:.4f} SOL**\n"
            f"🔹 Active Trades: **{active_trades}**\n"
            f"🔹 Monitoring: **{groups_count} Telegram groups**\n"
        )
        
        # Add buttons
        buttons = [
            [
                Button.inline("Enable Auto-Trade" if not self.trader.auto_trade_enabled else "Disable Auto-Trade", 
                             data="toggle_auto_trade")
            ],
            [
                Button.inline("View Settings", data="view_settings"),
                Button.inline("View Trades", data="view_trades")
            ]
        ]
        
        await self.send_message(
            event.chat_id,
            status_message,
            buttons=buttons
        )
    
    async def handle_settings(self, event):
        """
        Handle /settings command.
        
        Args:
            event: Telegram event
        """
        if not self.trader:
            await self.send_message(
                event.chat_id,
                "❌ Trader component not initialized"
            )
            return
        
        settings_message = (
            "⚙️ **Current Settings:**\n\n"
            f"🔹 Auto-Trading: **{'Enabled' if self.trader.auto_trade_enabled else 'Disabled'}**\n"
            f"🔹 Buy Amount: **{self.trader.buy_amount} SOL**\n"
            f"🔹 Target Multiplier: **{self.trader.target_multiplier}x**\n"
            f"🔹 Sell Percentage: **{self.trader.sell_percentage}%**\n"
        )
        
        # Add buttons
        buttons = [
            [
                Button.inline("Set Buy Amount", data="set_buy"),
                Button.inline("Set Target", data="set_target")
            ],
            [
                Button.inline("Set Sell %", data="set_sell"),
                Button.inline("Toggle Auto-Trade", data="toggle_auto_trade")
            ]
        ]
        
        await self.send_message(
            event.chat_id,
            settings_message,
            buttons=buttons
        )
    
    async def handle_trades(self, event):
        """
        Handle /trades command.
        
        Args:
            event: Telegram event
        """
        if not self.trader:
            await self.send_message(
                event.chat_id,
                "❌ Trader component not initialized"
            )
            return
        
        active_trades = self.trader.get_active_trades()
        
        if not active_trades:
            await self.send_message(
                event.chat_id,
                "📈 **Active Trades:**\n\nNo active trades at the moment."
            )
            return
        
        trades_message = "📈 **Active Trades:**\n\n"
        
        for i, trade in enumerate(active_trades, 1):
            trades_message += (
                f"**{i}. {trade['symbol']}**\n"
                f"🔹 Amount: {trade['amount']:.4f}\n"
                f"🔹 Current Value: {trade['current_value']:.4f} SOL\n"
                f"🔹 Profit: {trade['profit_percentage']:.2f}%\n\n"
            )
        
        await self.send_message(
            event.chat_id,
            trades_message
        )
    
    async def handle_enable(self, event):
        """
        Handle /enable command.
        
        Args:
            event: Telegram event
        """
        if not self.trader:
            await self.send_message(
                event.chat_id,
                "❌ Trader component not initialized"
            )
            return
        
        self.trader.set_auto_trade_enabled(True)
        
        await self.send_message(
            event.chat_id,
            "✅ Auto-trading has been **enabled**."
        )
    
    async def handle_disable(self, event):
        """
        Handle /disable command.
        
        Args:
            event: Telegram event
        """
        if not self.trader:
            await self.send_message(
                event.chat_id,
                "❌ Trader component not initialized"
            )
            return
        
        self.trader.set_auto_trade_enabled(False)
        
        await self.send_message(
            event.chat_id,
            "❌ Auto-trading has been **disabled**."
        )
    
    async def handle_set_buy(self, event):
        """
        Handle /setbuy command.
        
        Args:
            event: Telegram event
        """
        if not self.trader:
            await self.send_message(
                event.chat_id,
                "❌ Trader component not initialized"
            )
            return
        
        try:
            # Extract amount from command
            command = event.raw_text.split()
            
            if len(command) < 2:
                await self.send_message(
                    event.chat_id,
                    "❌ Please specify an amount: /setbuy <amount>"
                )
                return
            
            amount = float(command[1])
            
            if amount <= 0:
                await self.send_message(
                    event.chat_id,
                    "❌ Amount must be greater than 0."
                )
                return
            
            self.trader.set_buy_amount(amount)
            
            await self.send_message(
                event.chat_id,
                f"✅ Buy amount set to **{amount} SOL**."
            )
        
        except ValueError:
            await self.send_message(
                event.chat_id,
                "❌ Invalid amount. Please specify a valid number."
            )
        
        except Exception as e:
            logger.error(f"Error handling setbuy command: {str(e)}")
            await self.send_message(
                event.chat_id,
                "❌ An error occurred while setting buy amount."
            )
    
    async def handle_set_target(self, event):
        """
        Handle /settarget command.
        
        Args:
            event: Telegram event
        """
        if not self.trader:
            await self.send_message(
                event.chat_id,
                "❌ Trader component not initialized"
            )
            return
        
        try:
            # Extract multiplier from command
            command = event.raw_text.split()
            
            if len(command) < 2:
                await self.send_message(
                    event.chat_id,
                    "❌ Please specify a multiplier: /settarget <multiplier>"
                )
                return
            
            multiplier = float(command[1])
            
            if multiplier <= 1:
                await self.send_message(
                    event.chat_id,
                    "❌ Multiplier must be greater than 1."
                )
                return
            
            self.trader.set_target_multiplier(multiplier)
            
            await self.send_message(
                event.chat_id,
                f"✅ Target multiplier set to **{multiplier}x**."
            )
        
        except ValueError:
            await self.send_message(
                event.chat_id,
                "❌ Invalid multiplier. Please specify a valid number."
            )
        
        except Exception as e:
            logger.error(f"Error handling settarget command: {str(e)}")
            await self.send_message(
                event.chat_id,
                "❌ An error occurred while setting target multiplier."
            )
    
    async def handle_set_sell(self, event):
        """
        Handle /setsell command.
        
        Args:
            event: Telegram event
        """
        if not self.trader:
            await self.send_message(
                event.chat_id,
                "❌ Trader component not initialized"
            )
            return
        
        try:
            # Extract percentage from command
            command = event.raw_text.split()
            
            if len(command) < 2:
                await self.send_message(
                    event.chat_id,
                    "❌ Please specify a percentage: /setsell <percentage>"
                )
                return
            
            percentage = float(command[1])
            
            if percentage <= 0 or percentage > 100:
                await self.send_message(
                    event.chat_id,
                    "❌ Percentage must be between 0 and 100."
                )
                return
            
            self.trader.set_sell_percentage(percentage)
            
            await self.send_message(
                event.chat_id,
                f"✅ Sell percentage set to **{percentage}%**."
            )
        
        except ValueError:
            await self.send_message(
                event.chat_id,
                "❌ Invalid percentage. Please specify a valid number."
            )
        
        except Exception as e:
            logger.error(f"Error handling setsell command: {str(e)}")
            await self.send_message(
                event.chat_id,
                "❌ An error occurred while setting sell percentage."
            )
    
    async def handle_button(self, event):
        """
        Handle button callbacks.
        
        Args:
            event: Telegram event
        """
        if not self.trader:
            await event.answer("Trader component not initialized", alert=True)
            return
        
        try:
            # Get button data
            data = event.data.decode("utf-8")
            
            if data == "toggle_auto_trade":
                # Toggle auto-trade
                new_state = not self.trader.auto_trade_enabled
                self.trader.set_auto_trade_enabled(new_state)
                
                await event.answer(f"Auto-trading {'enabled' if new_state else 'disabled'}")
                
                # Update message
                await self.handle_status(event)
            
            elif data == "view_settings":
                # Show settings
                await self.handle_settings(event)
            
            elif data == "view_trades":
                # Show trades
                await self.handle_trades(event)
            
            elif data == "set_buy":
                # Prompt for buy amount
                await self.send_message(
                    event.chat_id,
                    "Please enter buy amount in SOL using /setbuy <amount>"
                )
            
            elif data == "set_target":
                # Prompt for target multiplier
                await self.send_message(
                    event.chat_id,
                    "Please enter target multiplier using /settarget <multiplier>"
                )
            
            elif data == "set_sell":
                # Prompt for sell percentage
                await self.send_message(
                    event.chat_id,
                    "Please enter sell percentage using /setsell <percentage>"
                )
            
            elif data.startswith("trade_"):
                # Handle token trade button
                token_data = data.split("_")[1:]
                if len(token_data) >= 2:
                    symbol = token_data[0]
                    address = token_data[1]
                    
                    # Buy token
                    success = await self.trader.buy_token(symbol, address)
                    
                    if success:
                        await event.answer(f"Started trading {symbol}")
                        await self.send_message(
                            event.chat_id,
                            f"✅ Successfully started trading **{symbol}**."
                        )
                    else:
                        await event.answer(f"Failed to trade {symbol}")
                        await self.send_message(
                            event.chat_id,
                            f"❌ Failed to start trading **{symbol}**."
                        )
                else:
                    await event.answer("Invalid token data")
            
            else:
                await event.answer("Unknown button")
        
        except Exception as e:
            logger.error(f"Error handling button callback: {str(e)}")
            await event.answer("An error occurred")
