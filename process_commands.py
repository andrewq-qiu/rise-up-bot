"""Module containing functions for processing
parameters given by the /rise up command.
"""

import datetime
import global_vars as gv
from typing import Optional
from dataclasses import dataclass


@dataclass
class Game:
    """A class representing a game."""
    name: str
    img_path: str


def get_datetime_now() -> datetime.datetime:
    """Return a timezone adjusted datetime.datetime
    value representing now.
    """

    return datetime.datetime.now(tz=gv.TIMEZONE)


def get_time_until(target: datetime.datetime):
    """Return the time in seconds from now
    to a given datetime

    Preconditions:
        - get_datetime_now() < target
    """
    return (target - get_datetime_now()).total_seconds()


def get_next_time(hour: int, minute: int):
    """Return the next datetime.datetime occurrence
    of an hour and minute.


    Parameter time must be in format:
        time: 'HH:MMpm' or 'HH:MMam'
    """

    now = get_datetime_now()
    target = now.replace(hour=hour, minute=minute, second=0)

    if target < now:
        target = target + datetime.timedelta(days=1)

    return target


def get_game(game_name: str) -> Game:
    """Return a Game instance containing
    the full game name and image path
    given a game_name str.
    """

    games = gv.GAMES

    if game_name in games:
        name = games[game_name]['name']
        img_path = games[game_name]['img']
    else:
        name = game_name
        img_path = ''

    return Game(name=name, img_path=img_path)


def get_datetime_from_time_str(time_str) -> Optional[datetime.datetime]:
    """Return a datetime.datetime object given
    a time_str. Return None if it was unsuccessful.

    The time_str must be in the format HH:MMpm or HH:MMam
    """

    # Check length of string (minimum 3 chars)
    if len(time_str) < 3:
        return None

    # Check Legal Characters
    legal_time_chars = ":0123456789"
    for char in time_str[:-2]:
        if char not in legal_time_chars:
            return None

    # Ensure that string ends in am or pm
    am_pm = time_str[-2:]
    if am_pm != 'am' and am_pm != 'pm':
        return None

    if ':' in time_str:
        time_split = time_str[:-2].split(':')

        # Ensure that there are two elements in the split string
        if len(time_split) != 2:
            return None

        hr = int(time_split[0])
        mins = int(time_split[1])

        if am_pm == 'pm':
            hr = (hr + 12) % 24

        return get_next_time(hour=hr, minute=mins)

    else:
        hr = int(time_str[:-2])
        if am_pm == 'pm':
            hr += 12

        return get_next_time(hour=hr, minute=0)


