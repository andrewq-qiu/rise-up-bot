"""Module for interacting with the Discord API
to generate the slash commands needed.

Run this file to update the slash commands for your bot
given settings in properties.json. It may take several hours
for it to fully update.
"""

import requests
from global_vars import load_json

PROPERTIES = load_json("properties.json")

url = PROPERTIES['bot_commands_url']

rise_up_json = {
    "name": "rise",
    "description": "Call a rise up",
    "options": [
        {
            "name": "up",
            "description": "Call a rise up",
            "type": 1,
            "options": [
                {
                    "name": "game",
                    "description": "The name of the game (ex. cs, forest)",
                    "type": 3,
                    "required": True
                },
                {
                    "name": "time",
                    "description": "The time for the rise (ex. 8pm, 9:01am)",
                    "type": 3,
                    "required": True
                },
                {
                    "name": "slots",
                    "description": "The number of slots for the rise",
                    "type": 4,
                    "required": True
                }
            ]
        }
    ]
}

change_time_json = {
    "name": "change",
    "description": "Change the time for an active rise",
    "options": [
        {
            "name": "time",
            "description": "Change the time for an active rise",
            "type": 1,
            "options": [
                {
                    "name": "time",
                    "description": "The new time for the rise (ex. 8pm, 9:01am)",
                    "type": 3,
                    "required": True
                }
            ]
        }
    ]
}

cancel_json = {
    "name": "cancel",
    "description": "Cancels an active rise",
    "options": []
}

close_json = {
    "name": "close",
    "description": "Closes an active rise",
    "options": []
}


force_setup_json = {
    "name": "force",
    "description": "(ADMIN) Resets stored information for a server",
    "options": [
        {
            "name": "setup",
            "description": "(ADMIN) Resets stored information for a server",
            "type": 1,
            "options": []
        }
    ]
}

usurp_json = {
    "name": "usurp",
    "description": "(ADMIN) Take control of another user's rise",
    "options": [
        {
            "name": "user",
            "description": "The target user to take the rise from",
            "type": 6,
            "required": True
        }
    ]
}


headers = {
    "Authorization": f"Bot {PROPERTIES['token']}"
}

# Send Requests to Add Commands To Server
r1 = requests.post(url, headers=headers, json=rise_up_json)
r2 = requests.post(url, headers=headers, json=change_time_json)
r3 = requests.post(url, headers=headers, json=cancel_json)
r4 = requests.post(url, headers=headers, json=close_json)
r5 = requests.post(url, headers=headers, json=force_setup_json)
r6 = requests.post(url, headers=headers, json=usurp_json)