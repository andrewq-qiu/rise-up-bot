from datetime import datetime
import discord
import imgkit
from rise_up import AvailabilityType, RiseUpData, RiseUpInteractor

def get_avatar_url(user: discord.Member) -> str:
    """Return a url for the avatar image of a given user."""

    return "https://cdn.discordapp.com/avatars/{0.id}/{0.avatar}.png?size=1024".format(user)

def datetime_to_short_str(date_time: datetime.datetime):
    hour = (((date_time.hour - 1) % 12) + 1)
    return str(hour) + date_time.strftime(':%M%p').lower()

def gen_interactor_html(interactor: RiseUpInteractor):
    """Generate an HTML Entry for an interactor"""

    if interactor.availability_type == AvailabilityType.LATE:
        return f"<div class='player'><img src='{get_avatar_url(interactor.user)}' " \
                    "class='player-image'><p class='player-name'>" \
                    f"{interactor.user.name}</p><img src='assets/clock.png' " \
                    "class='small-icon'></div>"
    else:
        return f"<div class='player'><img src='{get_avatar_url(interactor.user)}' " \
                    f"class='player-image'><p class='player-name'>{interactor.user.name}</p></div>"


def render_to_file(card_data: RiseUpData, path: str='cached_card.png'):
    """Render the Card from the HTML template into
    an image. Store the image into the given path.
    """

    my_html = open("sample.html", "r").read()

    # Add Initiator User Information
    my_html = my_html.replace("|sender_name|", card_data.author.name)
    my_html = my_html.replace("|sender_img|", get_avatar_url(card_data.author))

    # Add Game Information
    my_html = my_html.replace("|game_name|", card_data.game.name)
    my_html = my_html.replace("|game_time|",
                                datetime_to_short_str(card_data.target_time))
    my_html = my_html.replace("|game_img|", card_data.game.img_path)

    # Add Slot Information
    my_html = my_html.replace("|player_count|", str(len(card_data.available)))
    my_html = my_html.replace("|slots|", str(card_data.slots))

    available_html = ''.join(gen_interactor_html(available) for available in card_data.available)
    unavailable_html = ''.join(gen_interactor_html(unavailable) for unavailable in card_data.unavailable)

    my_html = my_html.replace("|available_list|", available_html)
    my_html = my_html.replace("|unavailable_list|", unavailable_html)

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