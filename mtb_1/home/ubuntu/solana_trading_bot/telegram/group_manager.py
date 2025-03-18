"""
Group manager for Telegram integration.
This module handles joining and managing Telegram groups.
"""
import asyncio
import re
from typing import List, Optional, Dict
from telethon import TelegramClient
from telethon.tl.functions.messages import ImportChatInviteRequest, CheckChatInviteRequest
from telethon.tl.functions.channels import JoinChannelRequest, GetFullChannelRequest
from telethon.errors import (
    UserAlreadyParticipantError,
    InviteHashEmptyError,
    InviteHashExpiredError,
    InviteHashInvalidError,
    FloodWaitError,
    ChannelPrivateError
)
from loguru import logger

class TelegramGroupManager:
    """
    Manager for Telegram groups.
    Handles joining and managing Telegram groups.
    """
    
    def __init__(self, client: TelegramClient):
        """
        Initialize the group manager.
        
        Args:
            client: Telethon client instance (user client)
        """
        self.client = client
        self.joined_groups = {}
        logger.info("Telegram group manager initialized")
    
    async def join_group(self, group_link: str) -> Optional[Dict]:
        """
        Join a Telegram group using an invite link.
        
        Args:
            group_link: Invite link for the group (e.g., https://t.me/group or https://t.me/joinchat/hash)
        
        Returns:
            Optional[Dict]: Group information if joined successfully, None otherwise
        """
        logger.info(f"Attempting to join group: {group_link}")
        
        try:
            # Clean and validate the link
            group_link = self._clean_group_link(group_link)
            if not group_link:
                logger.error("Invalid group link format")
                return None
            
            # Check if it's a public group or private group
            if 'joinchat' in group_link:
                # Private group with invite hash
                return await self._join_private_group(group_link)
            else:
                # Public group with username
                return await self._join_public_group(group_link)
        
        except FloodWaitError as e:
            # Handle rate limiting
            wait_time = e.seconds
            logger.warning(f"Rate limited when joining group. Need to wait {wait_time} seconds")
            await asyncio.sleep(wait_time)
            return await self.join_group(group_link)
        
        except Exception as e:
            logger.error(f"Failed to join group {group_link}: {str(e)}")
            return None
    
    async def _join_private_group(self, group_link: str) -> Optional[Dict]:
        """
        Join a private Telegram group using an invite hash.
        
        Args:
            group_link: Invite link for the private group
        
        Returns:
            Optional[Dict]: Group information if joined successfully, None otherwise
        """
        try:
            # Extract the hash from the invite link
            invite_hash = group_link.split('/')[-1]
            
            # Check the invite before joining
            try:
                invite_info = await self.client(CheckChatInviteRequest(invite_hash))
                logger.info(f"Invite info: {invite_info.title}")
            except Exception as e:
                logger.warning(f"Could not check invite info: {str(e)}")
            
            # Try to join the group
            try:
                updates = await self.client(ImportChatInviteRequest(invite_hash))
                
                # Extract group info from the updates
                for update in updates.updates:
                    if hasattr(update, 'chat_id'):
                        chat_id = update.chat_id
                        chat = await self.client.get_entity(chat_id)
                        
                        group_info = {
                            'id': chat_id,
                            'title': getattr(chat, 'title', 'Unknown'),
                            'username': getattr(chat, 'username', None),
                            'invite_link': group_link,
                            'member_count': getattr(chat, 'participants_count', 0)
                        }
                        
                        # Store in joined groups
                        self.joined_groups[chat_id] = group_info
                        
                        logger.info(f"Successfully joined private group: {group_info['title']}")
                        return group_info
            
            except UserAlreadyParticipantError:
                logger.info("Already a member of this group")
                
                # Try to get group info
                try:
                    # We need to find the chat ID from the invite hash
                    # This is a bit tricky, but we can try to get it from the updates
                    invite_info = await self.client(CheckChatInviteRequest(invite_hash))
                    if hasattr(invite_info, 'chat'):
                        chat = invite_info.chat
                        chat_id = chat.id
                        
                        group_info = {
                            'id': chat_id,
                            'title': getattr(chat, 'title', 'Unknown'),
                            'username': getattr(chat, 'username', None),
                            'invite_link': group_link,
                            'member_count': getattr(chat, 'participants_count', 0)
                        }
                        
                        # Store in joined groups
                        self.joined_groups[chat_id] = group_info
                        
                        return group_info
                except Exception as e:
                    logger.error(f"Error getting group info: {str(e)}")
            
            except (InviteHashEmptyError, InviteHashExpiredError, InviteHashInvalidError) as e:
                logger.error(f"Invalid invite hash: {str(e)}")
            
            except Exception as e:
                logger.error(f"Error joining private group: {str(e)}")
            
            return None
        
        except Exception as e:
            logger.error(f"Error in _join_private_group: {str(e)}")
            return None
    
    async def _join_public_group(self, group_link: str) -> Optional[Dict]:
        """
        Join a public Telegram group using a username.
        
        Args:
            group_link: Invite link for the public group
        
        Returns:
            Optional[Dict]: Group information if joined successfully, None otherwise
        """
        try:
            # Extract the username from the link
            username = group_link.split('/')[-1]
            
            try:
                # Try to join the channel/group
                updates = await self.client(JoinChannelRequest(username))
                
                # Get the channel entity
                channel = await self.client.get_entity(username)
                
                # Get full channel info
                try:
                    full_channel = await self.client(GetFullChannelRequest(channel=channel))
                    member_count = full_channel.full_chat.participants_count
                except Exception as e:
                    logger.warning(f"Could not get full channel info: {str(e)}")
                    member_count = 0
                
                group_info = {
                    'id': channel.id,
                    'title': getattr(channel, 'title', 'Unknown'),
                    'username': username,
                    'invite_link': group_link,
                    'member_count': member_count
                }
                
                # Store in joined groups
                self.joined_groups[channel.id] = group_info
                
                logger.info(f"Successfully joined public group: {group_info['title']}")
                return group_info
            
            except UserAlreadyParticipantError:
                logger.info("Already a member of this group")
                
                # Get the channel entity
                channel = await self.client.get_entity(username)
                
                # Get full channel info
                try:
                    full_channel = await self.client(GetFullChannelRequest(channel=channel))
                    member_count = full_channel.full_chat.participants_count
                except Exception as e:
                    logger.warning(f"Could not get full channel info: {str(e)}")
                    member_count = 0
                
                group_info = {
                    'id': channel.id,
                    'title': getattr(channel, 'title', 'Unknown'),
                    'username': username,
                    'invite_link': group_link,
                    'member_count': member_count
                }
                
                # Store in joined groups
                self.joined_groups[channel.id] = group_info
                
                return group_info
            
            except ChannelPrivateError:
                logger.error("Cannot join private channel with username, need invite link")
            
            except Exception as e:
                logger.error(f"Error joining public group: {str(e)}")
            
            return None
        
        except Exception as e:
            logger.error(f"Error in _join_public_group: {str(e)}")
            return None
    
    def _clean_group_link(self, group_link: str) -> Optional[str]:
        """
        Clean and validate a group link.
        
        Args:
            group_link: Group link to clean
        
        Returns:
            Optional[str]: Cleaned group link or None if invalid
        """
        # Remove whitespace
        group_link = group_link.strip()
        
        # Check if it's a valid Telegram link
        if not group_link.startswith(('https://t.me/', 'http://t.me/', 't.me/')):
            # Try to add the prefix
            if not re.match(r'^[a-zA-Z0-9_]+$', group_link):
                logger.error(f"Invalid group link format: {group_link}")
                return None
            
            # Assume it's a username
            group_link = f"https://t.me/{group_link}"
        
        # Ensure it starts with https
        if group_link.startswith('t.me/'):
            group_link = f"https://{group_link}"
        elif group_link.startswith('http://'):
            group_link = group_link.replace('http://', 'https://')
        
        return group_link
    
    async def leave_group(self, group_id: int) -> bool:
        """
        Leave a Telegram group.
        
        Args:
            group_id: ID of the group to leave
        
        Returns:
            bool: True if left successfully, False otherwise
        """
        try:
            # Get the group entity
            group = await self.client.get_entity(group_id)
            
            # Leave the group
            await self.client.delete_dialog(group)
            
            # Remove from joined groups
            if group_id in self.joined_groups:
                del self.joined_groups[group_id]
            
            logger.info(f"Successfully left group: {getattr(group, 'title', 'Unknown')}")
            return True
        
        except Exception as e:
            logger.error(f"Error leaving group {group_id}: {str(e)}")
            return False
    
    async def get_group_info(self, group_id: int) -> Optional[Dict]:
        """
        Get information about a joined group.
        
        Args:
            group_id: ID of the group
        
        Returns:
            Optional[Dict]: Group information or None if not found
        """
        # Check if we have it cached
        if group_id in self.joined_groups:
            return self.joined_groups[group_id]
        
        try:
            # Get the group entity
            group = await self.client.get_entity(group_id)
            
            # Get full channel info if it's a channel
            try:
                full_channel = await self.client(GetFullChannelRequest(channel=group))
                member_count = full_channel.full_chat.participants_count
            except Exception as e:
                logger.warning(f"Could not get full channel info: {str(e)}")
                member_count = 0
            
            group_info = {
                'id': group_id,
                'title': getattr(group, 'title', 'Unknown'),
                'username': getattr(group, 'username', None),
                'invite_link': f"https://t.me/{group.username}" if getattr(group, 'username', None) else None,
                'member_count': member_count
            }
            
            # Store in joined groups
            self.joined_groups[group_id] = group_info
            
            return group_info
        
        except Exception as e:
            logger.error(f"Error getting group info for {group_id}: {str(e)}")
            return None
    
    async def get_joined_groups(self) -> List[Dict]:
        """
        Get a list of all joined groups.
        
        Returns:
            List[Dict]: List of group information dictionaries
        """
        # Update the cache with the latest information
        try:
            dialogs = await self.client.get_dialogs()
            
            for dialog in dialogs:
                if dialog.is_group or dialog.is_channel:
                    # Get group info
                    await self.get_group_info(dialog.id)
        
        except Exception as e:
            logger.error(f"Error getting dialogs: {str(e)}")
        
        # Return the cached groups
        return list(self.joined_groups.values())
