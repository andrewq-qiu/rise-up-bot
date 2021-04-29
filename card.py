"""Module containing the Card class. Contains methods
for representing a rise up card and handling its
creation, interaction, and deletion.
"""

from typing import List
from functools import cmp_to_key
from dataclasses import dataclass
import discord
import imgkit
from rise_up import *
import global_vars as gv


async def delete_message(message):
    await message.delete()


def get_avatar_url(user) -> str:
    """Return a url for the avatar image of a given user."""

    return "https://cdn.discordapp.com/avatars/{0.id}/{0.avatar}.png?size=1024".format(user)


@dataclass
class AvailabilityType:
    """A class containing information regarding the availability
    of a participant: when they registered and their status.
    """
    time: datetime.datetime
    status: str


class Card:
    """A class representing a Rise Up card.

    Instance Attributes:
        - target_time: the targeted time for the rise
        - game: the game of the rise
        - slots: the number of slots
        - author: the discord.Member who initiated the rise
        - channel: the channel the rise is initiated in
    """

    def __init__(self, target_time: datetime.datetime, game: Game,
                 slots: int, author: discord.Member, channel: discord.TextChannel, ctx):
        """"""

        # =====================================================
        # INITIALIZE ATTRIBUTES
        # =====================================================

        self.target_time = target_time
        self.game = game
        self.slots = slots
        self.ctx = ctx

        # TYPE = discord.py Member
        self.author = author
        self.channel = channel

        self.players = {}
        self.players_availability_type = {}

        self.message = None
        self.cache_message = None
        self.forwarded_message = None

        self.guild = self.channel.guild

        # =====================================================
        # INITIALIZE TIMERS
        # =====================================================

        target_time_seconds = get_time_until(self.target_time)
        print(f"> Creating Notification Timer (Execution in {target_time_seconds}s)")
        self.notification_timer = gv.Timer(target_time_seconds, self.notify)

        delete_time_seconds = target_time_seconds + int(gv.PROPERTIES["close_rise_delay"])
        self.delete_timer = gv.Timer(delete_time_seconds, self.close)

    def render_to_file(self, path: str = 'card.png'):
        """Render the Card from the HTML template into
        an image. Store the image into the given path.
        """

        my_html = open("sample.html", "r").read()
        players = self.get_sorted_players()

        # Add Initiator User Information
        my_html = my_html.replace("|sender_name|", self.author.name)
        my_html = my_html.replace("|sender_img|", get_avatar_url(self.author))

        # Add Game Information
        my_html = my_html.replace("|game_name|", self.game.name)
        my_html = my_html.replace("|game_time|",
                                  datetime_to_short_str(self.target_time))
        my_html = my_html.replace("|game_img|", self.game.img_path)

        # Add Slot Information
        my_html = my_html.replace("|player_count|", str(len(players)))
        my_html = my_html.replace("|slots|", str(self.slots))

        # Add New Users
        template_available = "<div class='player'><img src='|player_image|' " \
                             "class='player-image'><p class='player-name'>|player_name|</p></div>"
        template_eating = "<div class='player'><img src='|player_image|' " \
                          "class='player-image'><p class='player-name'>" \
                          "|player_name|</p><img src='assets/fork.png' " \
                          "class='small-eating-icon'></div>"
        to_add = ""

        for player in players:
            player_id = str(player.id)
            status = self.players_availability_type[player_id].status

            player_html = ""

            if status == "Available":
                player_html = template_available.replace("|player_image|", get_avatar_url(player))
            elif status == "Eating":
                player_html = template_eating.replace("|player_image|", get_avatar_url(player))

            player_html = player_html.replace("|player_name|", player.name)

            to_add += player_html

        my_html = my_html.replace("|player_list|", to_add)

        options = {
            "format": "png",
            "disable-smart-width": "",
            "width": 400,
            "quiet": "",
            "enable-local-file-access": None
        }

        # Send MY_HTML to file for asset context
        with open("card.html", "w") as f:
            f.write(my_html)

        imgkit.from_file("card.html", path, config=gv.IMGKIT_CONFIG, options=options)

    async def send(self):
        """Send the Card to the cache, target, and forwarding (rise up)
        channel and update the global variables.
        """

        print("> Rise initiated by ", self.author.name)
        self.render_to_file()

        # Send New Cache Message
        self.cache_message = await gv.CACHE_CHANNEL.send(file=discord.File("card.png"))
        url = self.cache_message.attachments[0].url

        # Send Message to Target Channel
        await self.ctx.send(content=str(url))
        async for message in self.channel.history():
            if message.author == gv.CLIENT.user:
                self.message = message
                break

        guild_id = str(self.guild.id)
        author_id = str(self.author.id)

        # Add Card to the Global Variables
        gv.CARD_MESSAGES[str(self.message.id)] = author_id
        gv.CARDS[author_id] = self

        # Duplicate and Forward Message to Rise Up Channel
        if guild_id not in gv.GUILD_DATA:
            error_message = "The bot was not setup to forward rise up cards " \
                            "to a preset channel. To force a setup, try !force setup"

            await self.channel.send(error_message)
        else:
            rise_up_channel_id = int(gv.GUILD_DATA[guild_id]["rise_up_channel"])
            rise_up_channel = gv.CLIENT.get_channel(rise_up_channel_id)

            self.forwarded_message = await rise_up_channel.send(url)

            await self.forwarded_message.add_reaction("\u2705")
            await self.forwarded_message.add_reaction(u"\U0001F374")

            gv.CARD_MESSAGES[str(self.forwarded_message.id)] = author_id

        await self.message.add_reaction("\u2705")
        await self.message.add_reaction(u"\U0001F374")

    async def update(self):
        """Re-render card images and edit rise up messages."""

        # Delete the old cached message after 60s
        timer = gv.Timer(60, delete_message, [self.cache_message])
        self.render_to_file()

        # Send New Cache Message
        self.cache_message = await gv.CACHE_CHANNEL.send(file=discord.File('card.png'))
        image_url = self.cache_message.attachments[0].url

        await self.message.edit(content=image_url)

        if self.forwarded_message is not None:
            await self.forwarded_message.edit(content=image_url)

    def change_author(self, author: discord.Member):
        """Change the author of the rise and update gv.CARDS
        and gv.CARD_MESSAGES
        """
        old_author_id = str(self.author.id)
        author_id = str(author.id)

        del gv.CARDS[old_author_id]
        gv.CARDS[author_id] = self

        gv.CARD_MESSAGES[str(self.message.id)] = author_id
        gv.CARD_MESSAGES[str(self.forwarded_message.id)] = author_id

        self.author = author
        self.update()

    async def update_timers(self):
        """Updates the timers after the card's time has changed."""

        print("> Rise time updated by ", self.author.name)

        self.notification_timer.delete()
        self.delete_timer.delete()

        target_time_seconds = get_time_until(self.target_time)
        self.notification_timer = gv.Timer(target_time_seconds, self.notify)
        print(f"> Replacing Notification Timer (Execution in {target_time_seconds}s)")

        delete_time_seconds = target_time_seconds + int(gv.PROPERTIES["close_rise_delay"])
        self.delete_timer = gv.Timer(delete_time_seconds, self.close)

    async def notify(self):
        """Notifies the participants to the rise up."""

        print("> Notifying rise by", self.author.name)

        to_send = ''

        for key in self.players:
            player = self.players[key]
            to_send += f'<@{str(player.id)}> '

        target_time = datetime_to_short_str(self.target_time)
        to_send += f'\n{target_time} reminder.'

        await self.message.channel.send(to_send)

    async def delete(self):
        """Deletes the rise up and card."""

        print("> !CRITICAL Deleting rise by", self.author.name)

        del gv.CARD_MESSAGES[str(self.message.id)]
        del gv.CARD_MESSAGES[str(self.forwarded_message.id)]

        await self.message.delete()
        timer = gv.Timer(60, delete_message, [self.cache_message])

        if self.forwarded_message is not None:
            await self.forwarded_message.delete()

        del gv.CARDS[str(self.author.id)]
        self.notification_timer.delete()
        self.delete_timer.delete()
        del self

    async def close(self):
        """Closes the rise up and deletes the card."""
        print("> Closing rise by", self.author.name)

        # Generate Closing Text
        player_list = ""
        for key in self.players:
            player = self.players[key]
            player_list += f" - {player.name}\n"

        target_time = datetime_to_short_str(self.target_time)

        start = f"```md\n# Closed Rise Up\n{self.author.name} played {self.game.name} at [ {target_time} ]."
        end = f"\n\nParticipants:\n{player_list}```"

        del gv.CARD_MESSAGES[str(self.message.id)]
        del gv.CARD_MESSAGES[str(self.forwarded_message.id)]

        await self.message.edit(content=start + end)
        timer = gv.Timer(60, delete_message, self.cache_message)

        if self.forwarded_message is not None:
            await self.forwarded_message.delete()

        del gv.CARDS[str(self.author.id)]
        self.notification_timer.delete()
        self.delete_timer.delete()
        del self

    def get_players(self) -> List[discord.Member]:
        """Return the list of players"""
        return [self.players[key] for key in self.players]

    def get_sorted_players(self) -> List[discord.Member]:
        """Return the sorted list of players"""

        # Define a function to compare two players
        def compare_players(a, b):
            time_a = self.players_availability_type[str(a.id)].time
            time_b = self.players_availability_type[str(b.id)].time

            if time_a > time_b:
                return 1
            elif time_a == time_b:
                return 0
            else:
                return -1

        players = self.get_players()

        return sorted(players, key=cmp_to_key(compare_players))