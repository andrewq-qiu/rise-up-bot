"""Module for handling global variables for the
rise up bot.

Global Variables:
    - GAMES: a dictionary containing stored game information
    - PROPERTIES: the bot properties
    - GUILD_DATA: the stored data for the bot's guilds
    - TIMEZONE: the pytz.timezone object for the main timezone of the bot
    - CARD_MESSAGES: a dictionary mapping message_ids to the card represented by the message
    - CARDS: a dictionary mapping an author id to their active rise
    - CACHE_CHANNEL: the channel the bot uses for caching images
    - READY: whether or not the bot has loaded into discord servers
    - IMGKIT_CONFIG: the imgkit config storing the wkhtmltopdf path
"""

from __future__ import annotations
from typing import Optional, Dict
import datetime
import json
import os
import discord
import imgkit
import asyncio
import pytz
from card import Card


from discord.ext import commands
CLIENT = commands.Bot(command_prefix='/', intents=discord.Intents.all())


class DummyMessage:
    """Class imitating a discord.Message for testing purposes

    Instance Attributes:
        - content: the content of the message
    """
    content: str

    def __init__(self, content: str):
        """Initialize the dummy message"""
        self.content = content


class DummyAvatar:
    """Class imitating a discord.User for testing purposes

    Instance Attributes:
        - name: the name of the user
        - avatar_url: the url of the avatar image
    """
    name: str
    avatar_url: str

    def __init__(self, name: str, avatar_url: str):
        """Initialize the dummy avatar"""
        self.name = name
        self.avatar_url = avatar_url


class Timer:
    """A class with methods for handling asynchronous functions
    executed after a set amount of time.
    """

    def __init__(self, timeout: int, callback, args: Optional[list] = None, kw_args: Optional[dict] = None):
        """Initialize the timer"""

        if kw_args is None:
            kw_args = {}
        self._timeout = timeout
        self._callback = callback
        self._task = asyncio.ensure_future(self._job())
        self.deleted = False

        self.args = args
        self.kw_args = kw_args

    def delete(self):
        """Delete the timer and prevent execution"""
        self.deleted = True

    async def _job(self):
        """(PRIVATE) Execute the timed function"""
        await asyncio.sleep(self._timeout)

        if self.deleted:
            print("|| Timer called but was deleted!")
            del self
            return

        print("|| Timer called and is being executed...")

        if self.args is None:
            if self.kw_args is None:
                await self._callback()
            else:
                await self._callback(**self.kw_args)
        else:
            if self.kw_args is None:
                await self._callback(*self.args)
            else:
                await self._callback(*self.args, **self.kw_args)


def load_json(path):
    """Load and return a json file given a path."""
    f = open(path, "r")
    return json.loads(f.read())


def save_to_json(obj, path):
    """Dump an object into a specified json file."""
    with open(path, "w") as f:
        json.dump(obj, f)


async def refresh_message(message):
    """Refresh the information of a discord.Message"""
    return await message.channel.fetch_message(message.id)


# =====================================================
# DEFINE GLOBAL VARIABLES
# =====================================================

GAMES = load_json("games.json")
PROPERTIES = load_json("properties.json")
GUILD_DATA = load_json("guild_data.json")

pytz.utc.localize(datetime.datetime.utcnow()).astimezone(pytz.timezone('US/Pacific'))
TIMEZONE = pytz.timezone(PROPERTIES["timezone"])

# Dict mapping message ids to the author of the relevant rise.
CARD_MESSAGES = {}
# Dict mapping author ids to the card of the relevant rise.
CARDS = {}

CARD_MESSAGES: Dict[str, str]
CARDS: Dict[str, Card]

CACHE_CHANNEL = None

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
READY = False

if PROPERTIES["wkhtmltoimage_is_relative"]:
    _path = ROOT_DIR + PROPERTIES["wkhtmltoimage"]
else:
    _path = PROPERTIES["wkhtmltoimage"]

IMGKIT_CONFIG = imgkit.config(wkhtmltoimage=_path)