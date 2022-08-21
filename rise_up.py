"""Module containing the RiseUp class. Contains methods
for representing a rise up card and handling its
creation, interaction, and deletion.
"""

from enum import Enum
from dataclasses import dataclass
import discord
import interactions
from process_commands import *
import global_vars as gv
from render import datetime_to_short_str, render_to_file

class AvailabilityType(Enum):
    """An enum defining the types of availability a RiseUpInteractor can have with a Card"""
    AVAILABLE='available'
    LATE='late'
    UNAVAILABLE='unavailable'

@dataclass
class RiseUpInteractor:
    """A class describing a interactor to a RiseUp"""
    first_interacted_time: datetime.datetime
    availability_type: str
    user: discord.Member

@dataclass
class RiseUpData:
    """A class describing the basic data for a RiseUp"""
    # The scheduled rise up time
    scheduled_time: datetime.datetime
    # The game for the rise up
    game: Game
    # The number of slots available
    slots: int
    # The discord.Member who initiated the rise
    author: discord.Member
    # A list of available participants, sorted based on their first_interacted_time
    available: list[RiseUpInteractor]
    # A list of unavailable participants, sorted based on their first_interacted_time
    unavailable: list[RiseUpInteractor]

class RiseUp:
    """A class representing a rise up."""
    
    # The data the rise up is based upon
    rise_up_data: RiseUpData
    # The context for the command that initiated the rise
    _command_ctx: interactions.CommandContext
    # The main message sent to the channel where the command was called
    _message: discord.Message
    # The message sent to the cache channel for storing the image
    _cache_message: discord.Message
    # The message forwaded to the guild's dedicated "rise-up" channel
    _forwarded_message: discord.Message
    _notify_timer: gv.Timer
    _close_timer: gv.Timer

    def __init__(self, rise_up_data: RiseUpData, command_ctx: interactions.CommandContext):
        """Initialize the RiseUp
        
        Instance Attributes:
            - rise_up_data: the data the rise up is based upon
            - command_ctx: the context for the command that initiated the rise
        """
        
        self.rise_up_data = rise_up_data
        self._command_ctx = command_ctx
        self._message = None
        self._cache_message = None
        self._forwarded_message = None

    def _initialize_timers(self):
        """Initialize Timers for the notification and close events for the rise up."""
        
        notify_in_seconds = get_time_until(self.rise_up_data.scheduled_time)
        print(f"> Creating Notification Timer (Execution in {notify_in_seconds}s)")
        self._notify_timer = gv.Timer(notify_in_seconds, self.notify)

        close_in_seconds = notify_in_seconds + int(gv.PROPERTIES["close_rise_delay"])
        self._close_timer = gv.Timer(close_in_seconds, self.close)

    def delete_timers(self):
        """Delete the active timers associated to the RiseUp"""
        self._notify_timer.delete()
        self._close_timer.delete()
        
    async def refresh_timers(self):
        """Refresh the timers after the card's scheduled time has changed."""
        self.delete_timers()
        self._initialize_timers()

    async def _send_temporary_message(self):
        """Send a temporary message to the origin channel to be displayed
        while the card render is being rendered and uploaded.
        
        Update self._message to this temporary message.
        """

        await self._command_ctx.send("Creating a new Rise Up...")

        async for message in self._command_ctx.channel.history():
            if message.author == gv.CLIENT.user:
                self.message = message
                break

    async def _add_reactions_to(self, message: discord.Message):
        """Add the default reactions to a Rise Up! message."""

        await message.add_reaction("✅")
        await message.add_reaction("🕘")
        await message.add_reaction("❌")

    async def _update_messages_to_cache(self):
        """Send/Edit messages in the origin and forwarded channels
        to match the latest render in the cache channel.

        Preconditions:
            - self._message is not None
        """

        render_url = self._cache_message.attachments[0].url

        if self._forwarded_message is None:
            rise_up_channel_id = int(gv.GUILD_DATA[str(self.guild.id)]["rise_up_channel"])
            rise_up_channel = gv.CLIENT.get_channel(rise_up_channel_id)

            self.forwarded_message = await rise_up_channel.send(render_url)
        else:
            await self._forwarded_message.edit(content=render_url)

        self.message.edit(content=render_url)

    async def send(self):
        """Send the RiseUp card messages to the cache, origin, and rise-up (forwaded) channels.
        
        While the card is being rendered and uploaded to the cache channel,
        send a temporary message to the origin channel.
        """

        print("> Rise initiated by ", self.author.name)
        await self._send_temporary_message()

        self.update_render()
        self._add_reactions_to(self._message)
        self._add_reactions_to(self._forwarded_message)

    async def update_render(self):
        """Re-render card images and update the messages sent to the
        cache, origin, and forwaded channels."""

        # Render the card to a temporary file: "cached_card.png"
        render_to_file(self.rise_up_data)

        old_cache_message = self._cache_message

        # Send new cache message and update origin and forwaded messages
        self._cache_message = await gv.CACHE_CHANNEL.send(file=discord.File('cached_card.png'))
        self._update_messages_to_cache()
        
        # Remove old cache message
        await old_cache_message.delete()

    async def notify(self):
        """Send the notification message for the RiseUp"""
        print("> Notifying rise by", self.author.name)

        await self.message.channel.send(' '.join(f"<@{str(available.user.id)}>" for available in self.rise_up_data.available) 
            + f"\n{datetime_to_short_str(self.rise_up_data.scheduled_time)} reminder")

    async def close(self):
        """Close the RiseUp. Remove the latest render from the cache channel and 
        edit the origin and forwarded messages to a persistent text summary of the RiseUp.
        """
        print("> Closing rise by", self.author.name)

        player_list = "\n".join(f" - {available.user.id}" for available in self.rise_up_data.available)

        summary = (f"```md\n# Closed Rise Up"
                   f"\n{self.rise_up_data.author.name} played {self.rise_up_data.game.name}"
                   f"at [ {datetime_to_short_str(self.rise_up_data.scheduled_time)} ]."
                   f"\n\nParticipants:\n{player_list}```")

        await self._message.edit(content=summary)
        await self._forwarded_message.edit(content=summary)
        await self._cache_message.delete()