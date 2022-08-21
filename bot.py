"""Module for initializing and handling
interactions for the rise up bot
on discord.
"""


import global_vars as gv
import datetime
import discord

# NEW (Experimental) Discord Features
from discord.ext import commands
from discord_slash import SlashCommand
from discord_slash.model import SlashContext

import card
import process_commands


CLIENT = gv.CLIENT
slash = SlashCommand(CLIENT)


@CLIENT.event
async def on_ready() -> None:
    """This function is run when the discord bot has connected to discord."""

    print(f'{CLIENT.user} has connected to Discord!')
    gv.CACHE_CHANNEL = CLIENT.get_channel(int(gv.PROPERTIES["cache_channel"]))
    gv.READY = True

    await CLIENT.change_presence(activity=discord.Activity(
        type=discord.ActivityType.listening, name="!rise up"))


@slash.subcommand(base="rise", name="up")
async def _rise_up(ctx: SlashContext, game_name: str, time_str: str, slots: int) -> None:
    """This function handles the !rise up command.
    """

    game = process_commands.get_game(game_name)
    time = process_commands.get_datetime_from_time_str(time_str)

    if time is None:
        await ctx.send(content='You did not specify a valid time. Try something like this: 5pm, 9:01am.')
        return

    author_id = str(ctx.author.id)

    if author_id in gv.CARDS:
        # RiseUp already exists
        # Delete Old RiseUp
        print("> User initiated a new card while an old card is still active! Closing previous card...")
        await gv.CARDS[author_id].close()

    new_card = card.RiseUp(
        target_time=time, game=game, slots=slots, author=ctx.author, channel=ctx.channel, ctx=ctx)

    await new_card.send()


@slash.subcommand(base="change", name="time")
async def _change_time(ctx: SlashContext, time_str: str) -> None:
    """This function handles changing the time of an
    active rise.
    """

    user_id = str(ctx.author.id)
    time = process_commands.get_datetime_from_time_str(time_str)

    if user_id in gv.CARDS:
        if time is None:
            await ctx.send(content='You did not specify a valid time.'
                                   ' Try something like this: 5pm, 9:01am.')
            return
        else:
            my_card = gv.CARDS[user_id]

            my_card.target_time = time
            await my_card.update()
            await my_card.update_timers()
            await ctx.send(content=f'You have changed the time for the {my_card.game.name}'
                                   f'rise up to {process_commands.datetime_to_short_str(time)}.')

    else:
        await ctx.send(content="You don't have an active rise.")


@slash.slash(name="cancel")
async def _cancel(ctx: SlashContext) -> None:
    """This function handles canceling an active rise.
    """
    user_id = str(ctx.author.id)

    if user_id in gv.CARDS:
        await gv.CARDS[user_id].delete()
    else:
        await ctx.send(content="You don't have an active rise.")


@slash.slash(name="close")
async def _close(ctx: SlashContext) -> None:
    """This function handles closing an active rise.
    """
    user_id = str(ctx.author.id)

    if user_id in gv.CARDS:
        await gv.CARDS[user_id].close()
    else:
        await ctx.send(content="You don't have an active rise.")


@slash.subcommand(base="force", name="setup")
async def _force_setup(ctx: SlashContext) -> None:
    """This function handles forcing a setup of the bot on a guild.
    """

    # Check Bot Channels
    rise_up_channel_exists = False
    rise_up_channel = None
    guild = ctx.guild

    for channel in guild.text_channels:
        if channel.name.lower() == "rise-ups":
            rise_up_channel_exists = True
            rise_up_channel = channel

            break

    if not rise_up_channel_exists:
        rise_up_channel = await guild.create_text_channel("rise-ups")

    # Save Data
    gv.GUILD_DATA[str(guild.id)] = {"rise_up_channel": int(rise_up_channel.id)}
    gv.save_to_json(gv.GUILD_DATA, "guild_data.json")

    await ctx.send(content='The bot has successfully setup.')


@slash.slash(name="usurp")
async def _usurp(ctx: SlashContext, user: discord.Member) -> None:
    """This function handles usurping an active rise.
    """
    user_id = str(user.id)

    if user_id in gv.CARDS:
        my_card = gv.CARDS[user_id]
        my_card.change_author(user)

        await ctx.send(content=f'You have successfully stolen a rise from <@{user_id}>')

    else:
        await ctx.send(content="The targeted user does not have a rise.")


@slash.slash(name="give")
async def _give(ctx: SlashContext, user: discord.Member) -> None:
    """This function handles giving a rise to another user.
    """

    user_id = str(user.id)
    author_id = str(ctx.author.id)

    if user_id in gv.CARDS:
        await ctx.send(content='The target user already has a rise!')
    elif author_id in gv.CARDS:
        my_card = gv.CARDS[author_id]
        my_card.change_author(user)

        await ctx.send(content=f'You have successfully given your rise to <@{user_id}>')
    else:
        await ctx.send(content="You don't have a rise to give!")


@CLIENT.event
async def on_reaction_add(reaction, user):
    """This function handles reaction adding to rise up commands."""
    
    if not gv.READY:
        return

    if user.bot:
        return

    message_id = str(reaction.message.id)

    if message_id not in gv.CARD_MESSAGES:
        return

    if reaction.emoji == "✅":
        status = "Available"
    elif reaction.emoji == "🍴":
        status = "Eating"
    else:
        return

    user_id = str(user.id)

    # CASE 1: User Reacts but has already selected another option in the same message
    root_alt_reaction = None

    author_id = gv.CARD_MESSAGES[message_id]
    gv.CARDS[author_id].players[user_id] = user

    for r in reaction.message.reactions:
        if r.emoji != reaction.emoji:
            root_alt_reaction = r
            break

    async for u in root_alt_reaction.users():
        if user_id == str(u.id):
            # Delete Other Reaction
            await root_alt_reaction.remove(u)
            break

    # CASE 2: User Reacts but has already selected another option in a forwarded message
    if gv.CARDS[author_id].forwarded_message is not None:
        # Reacted on Source Message

        if str(gv.CARDS[author_id].message.id) == message_id:
            # Refresh Message Cache
            gv.CARDS[author_id].forwarded_message = await gv.refresh_message(gv.CARDS[author_id].forwarded_message)
            reactions = gv.CARDS[author_id].forwarded_message.reactions
        else:
            gv.CARDS[author_id].message = await gv.refresh_message(gv.CARDS[author_id].message)
            reactions = gv.CARDS[author_id].message.reactions

        terminate = False

        for r in reactions:
            async for u in r.users():
                if user_id == str(u.id):
                    # Delete Other Reaction
                    await r.remove(u)
                    terminate = True
                    break

            if terminate:
                break

    if user_id not in gv.CARDS[author_id].players_availability_type:
        gv.CARDS[author_id].players_availability_type[user_id] \
            = card.AvailabilityType(datetime.datetime.now(), status)
    else:
        gv.CARDS[author_id].players_availability_type[user_id].status = status

    await gv.CARDS[author_id].update()


@CLIENT.event
async def on_reaction_remove(reaction, user):
    """This function handles reaction removing to rise up commands."""
    
    if not gv.READY:
        return

    if user.bot:
        return

    message_id = str(reaction.message.id)

    if message_id not in gv.CARD_MESSAGES:
        return

    if not (reaction.emoji == "✅" or reaction.emoji == "🍴"):
        return

    user_id = str(user.id)

    # Check if user reacted to other emoticon
    other_reaction = None
    reacted_to_other = False

    author_id = gv.CARD_MESSAGES[message_id]

    for r in reaction.message.reactions:
        if r.emoji != reaction.emoji:
            other_reaction = r
            break

    async for u in other_reaction.users():
        if user_id == str(u.id):
            reacted_to_other = True
            break

    if not reacted_to_other and gv.CARDS[author_id].forwarded_message is not None:
        # Reacted on Source Message

        if str(gv.CARDS[author_id].message.id) == message_id:
            # Refresh Message Cache
            gv.CARDS[author_id].forwarded_message = await gv.refresh_message(gv.CARDS[author_id].forwarded_message)
            reactions = gv.CARDS[author_id].forwarded_message.reactions
        else:
            gv.CARDS[author_id].message = await gv.refresh_message(gv.CARDS[author_id].message)
            reactions = gv.CARDS[author_id].message.reactions

        for r in reactions:
            async for u in r.users():
                if user_id == str(u.id):
                    # Delete Other Reaction
                    reacted_to_other = True
                    break

            if reacted_to_other:
                break

    if not reacted_to_other:
        del gv.CARDS[author_id].players[user_id]
        print(f"{user_id} removed reaction message...")

        await gv.CARDS[author_id].update()


CLIENT.run(gv.PROPERTIES["token"])
