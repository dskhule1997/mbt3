"""
Telegram bot interface for Solana trading bot.
This module connects the Telegram bot with the trading logic.
"""
import asyncio
from typing import Dict, List, Optional
from telethon import Button
from loguru import logger

from telegram.bot_client import BotClient
from trading.solana_trader import SolanaTrader
from website_monitor.jup_monitor import JupTrenchesMonitor

class TelegramInterface:
    """
    Interface between Telegram bot and trading logic.
    Handles commands, notifications, and inline buttons.
    """
    
    def __init__(
        self,
        bot_client: BotClient,
        trader: SolanaTrader,
        jup_monitor: Optional[JupTrenchesMonitor] = None
    ):
        """
        Initialize the Telegram interface.
        
        Args:
            bot_client: Telegram bot client
            trader: Solana trader
            jup_monitor: Jupiter Trenches monitor (optional)
        """
        self.bot = bot_client
        self.trader = trader
        self.jup_monitor = jup_monitor
        self.admin_id = bot_client.admin_id
        
        # Register command handlers
        self._register_handlers()
        
        # Set notification callbacks
        if jup_monitor:
            jup_monitor.set_notification_callback(self.notify_token_detected)
        
        logger.info("Telegram interface initialized")
    
    def _register_handlers(self):
        """Register command handlers with the bot client."""
        # Register command handlers
        self.bot.register_command_handler("start", self._handle_start)
        self.bot.register_command_handler("help", self._handle_help)
        self.bot.register_command_handler("status", self._handle_status)
        self.bot.register_command_handler("settings", self._handle_settings)
        self.bot.register_command_handler("trades", self._handle_trades)
        self.bot.register_command_handler("enable", self._handle_enable)
        self.bot.register_command_handler("disable", self._handle_disable)
        self.bot.register_command_handler("setbuy", self._handle_set_buy)
        self.bot.register_command_handler("settarget", self._handle_set_target)
        self.bot.register_command_handler("setsell", self._handle_set_sell)
        
        # Register button callback handler
        self.bot.register_button_callback(self._handle_button)
        
        logger.info("Command handlers registered")
    
    async def _handle_start(self, event):
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
        
        await self.bot.client.send_message(
            event.chat_id,
            welcome_message
        )
    
    async def _handle_help(self, event):
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
        
        await self.bot.client.send_message(
            event.chat_id,
            help_message
        )
    
    async def _handle_status(self, event):
        """
        Handle /status command.
        
        Args:
            event: Telegram event
        """
        # Get wallet balance
        sol_balance = await self.trader.wallet.get_sol_balance()
        
        # Get active trades count
        active_trades = len(self.trader.active_trades)
        
        # Get auto-trade status
        auto_trade_status = "Enabled" if self.trader.auto_trade_enabled else "Disabled"
        
        status_message = (
            "📊 **Bot Status:**\n\n"
            f"🔹 Auto-Trading: **{auto_trade_status}**\n"
            f"🔹 SOL Balance: **{sol_balance:.4f} SOL**\n"
            f"🔹 Active Trades: **{active_trades}**\n"
            f"🔹 Monitoring: **{len(self.bot.user_client.groups)} Telegram groups**\n"
        )
        
        if self.jup_monitor:
            status_message += f"🔹 Website Monitoring: **Active**\n"
        
        # Add buttons
        buttons = [
            [
                Button.inline("Enable Auto-Trade" if not self.trader.auto_trade_enabled else "Disable Auto-Trade", 
                             data=f"toggle_auto_trade")
            ],
            [
                Button.inline("View Settings", data="view_settings"),
                Button.inline("View Trades", data="view_trades")
            ]
        ]
        
        await self.bot.client.send_message(
            event.chat_id,
            status_message,
            buttons=buttons
        )
    
    async def _handle_settings(self, event):
        """
        Handle /settings command.
        
        Args:
            event: Telegram event
        """
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
        
        await self.bot.client.send_message(
            event.chat_id,
            settings_message,
            buttons=buttons
        )
    
    async def _handle_trades(self, event):
        """
        Handle /trades command.
        
        Args:
            event: Telegram event
        """
        active_trades = self.trader.get_active_trades()
        
        if not active_trades:
            await self.bot.client.send_message(
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
        
        await self.bot.client.send_message(
            event.chat_id,
            trades_message
        )
    
    async def _handle_enable(self, event):
        """
        Handle /enable command.
        
        Args:
            event: Telegram event
        """
        self.trader.set_auto_trade_enabled(True)
        
        await self.bot.client.send_message(
            event.chat_id,
            "✅ Auto-trading has been **enabled**."
        )
    
    async def _handle_disable(self, event):
        """
        Handle /disable command.
        
        Args:
            event: Telegram event
        """
        self.trader.set_auto_trade_enabled(False)
        
        await self.bot.client.send_message(
            event.chat_id,
            "❌ Auto-trading has been **disabled**."
        )
    
    async def _handle_set_buy(self, event):
        """
        Handle /setbuy command.
        
        Args:
            event: Telegram event
        """
        try:
            # Extract amount from command
            command = event.raw_text.split()
            
            if len(command) < 2:
                await self.bot.client.send_message(
                    event.chat_id,
                    "❌ Please specify an amount: /setbuy <amount>"
                )
                return
            
            amount = float(command[1])
            
            if amount <= 0:
                await self.bot.client.send_message(
                    event.chat_id,
                    "❌ Amount must be greater than 0."
                )
                return
            
            self.trader.set_buy_amount(amount)
            
            await self.bot.client.send_message(
                event.chat_id,
                f"✅ Buy amount set to **{amount} SOL**."
            )
        
        except ValueError:
            await self.bot.client.send_message(
                event.chat_id,
                "❌ Invalid amount. Please specify a valid number."
            )
        
        except Exception as e:
            logger.error(f"Error handling setbuy command: {str(e)}")
            await self.bot.client.send_message(
                event.chat_id,
                "❌ An error occurred while setting buy amount."
            )
    
    async def _handle_set_target(self, event):
        """
        Handle /settarget command.
        
        Args:
            event: Telegram event
        """
        try:
            # Extract multiplier from command
            command = event.raw_text.split()
            
            if len(command) < 2:
                await self.bot.client.send_message(
                    event.chat_id,
                    "❌ Please specify a multiplier: /settarget <multiplier>"
                )
                return
            
            multiplier = float(command[1])
            
            if multiplier <= 1:
                await self.bot.client.send_message(
                    event.chat_id,
                    "❌ Multiplier must be greater than 1."
                )
                return
            
            self.trader.set_target_multiplier(multiplier)
            
            await self.bot.client.send_message(
                event.chat_id,
                f"✅ Target multiplier set to **{multiplier}x**."
            )
        
        except ValueError:
            await self.bot.client.send_message(
                event.chat_id,
                "❌ Invalid multiplier. Please specify a valid number."
            )
        
        except Exception as e:
            logger.error(f"Error handling settarget command: {str(e)}")
            await self.bot.client.send_message(
                event.chat_id,
                "❌ An error occurred while setting target multiplier."
            )
    
    async def _handle_set_sell(self, event):
        """
        Handle /setsell command.
        
        Args:
            event: Telegram event
        """
        try:
            # Extract percentage from command
            command = event.raw_text.split()
            
            if len(command) < 2:
                await self.bot.client.send_message(
                    event.chat_id,
                    "❌ Please specify a percentage: /setsell <percentage>"
                )
                return
            
            percentage = float(command[1])
            
            if percentage <= 0 or percentage > 100:
                await self.bot.client.send_message(
                    event.chat_id,
                    "❌ Percentage must be between 0 and 100."
                )
                return
            
            self.trader.set_sell_percentage(percentage)
            
            await self.bot.client.send_message(
                event.chat_id,
                f"✅ Sell percentage set to **{percentage}%**."
            )
        
        except ValueError:
            await self.bot.client.send_message(
                event.chat_id,
                "❌ Invalid percentage. Please specify a valid number."
            )
        
        except Exception as e:
            logger.error(f"Error handling setsell command: {str(e)}")
            await self.bot.client.send_message(
                event.chat_id,
                "❌ An error occurred while setting sell percentage."
            )
    
    async def _handle_button(self, event):
        """
        Handle button callbacks.
        
        Args:
            event: Telegram event
        """
        try:
            # Get button data
            data = event.data.decode("utf-8")
            
            if data == "toggle_auto_trade":
                # Toggle auto-trade
                new_state = not self.trader.auto_trade_enabled
                self.trader.set_auto_trade_enabled(new_state)
                
                await event.answer(f"Auto-trading {'enabled' if new_state else 'disabled'}")
                
                # Update message
                await self._handle_status(event)
            
            elif data == "view_settings":
                # Show settings
                await self._handle_settings(event)
            
            elif data == "view_trades":
                # Show trades
                await self._handle_trades(event)
            
            elif data == "set_buy":
                # Prompt for buy amount
                await self.bot.client.send_message(
                    event.chat_id,
                    "Please enter buy amount in SOL using /setbuy <amount>"
                )
            
            elif data == "set_target":
                # Prompt for target multiplier
                await self.bot.client.send_message(
                    event.chat_id,
                    "Please enter target multiplier using /settarget <multiplier>"
                )
            
            elif data == "set_sell":
                # Prompt for sell percentage
                await self.bot.client.send_message(
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
                        await self.bot.client.send_message(
                            event.chat_id,
                            f"✅ Successfully started trading **{symbol}**."
                        )
                    else:
                        await event.answer(f"Failed to trade {symbol}")
                        await self.bot.client.send_message(
                            event.chat_id,
                            f"❌ Failed to start trading **{symbol}**."
                        )
                else:
                    await event.answer("Invalid token data")
            
            else:
                await event.answer("Unknown button")
        
        except Exception as e:
            # Log the error
            logger.error(f"An unexpected error occurred: {str(e)}")
            
            # Optionally, send a message to the user (if this block is part of an async method)
            await self.bot.client.send_message(
                event.chat_id,
                "❌ An error occurred while processing your request. Please try again later."
            )
