import discord
from discord.ext import commands, tasks
import asyncio
import requests
import json
import logging
import colorlog

console_handler = colorlog.StreamHandler()
console_handler.setLevel(logging.DEBUG)

formatter = colorlog.ColoredFormatter(
    '%(asctime)s %(log_color)s%(levelname)s\t%(green)s%(name)s\t%(white)s%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    reset=True,
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'blue',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red,bg_white',
    }
)

console_handler.setFormatter(formatter)

root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
root_logger.addHandler(console_handler)


with open('config.json') as f:
    config = json.load(f)

with open('cat-contains.json') as f:
    cat_contains = json.load(f)

with open('cat-exact.json') as f:
    cat_exact = json.load(f)

intents = discord.Intents.default()
intents.presences = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

DISCORD_CHANNEL_ID = int(config["DISCORD_CHANNEL_ID"])
DISCORD_USER_ID = int(config["DISCORD_USER_ID"])
DISCORD_BOT_TOKEN = config["DISCORD_BOT_TOKEN"]
TWITCH_USER_ID = config["TWITCH_USER_ID"]
TWITCH_TOKEN = config["TWITCH_TOKEN"]
TWITCH_CLIENT_ID = config["TWITCH_CLIENT_ID"]

BASE_TWITCH_API_URL = 'https://api.twitch.tv/helix'

current_game = None
previous_game = None


def change_twitch_category(game_id):
    logging.info('Changing Twitch category' + "-" * 70)
    url = f'{BASE_TWITCH_API_URL}/channels'
    params = {
        'broadcaster_id': TWITCH_USER_ID
    }
    headers = {
        'Authorization': f'Bearer {TWITCH_TOKEN}',
        'Client-Id': TWITCH_CLIENT_ID,
        'Content-Type': 'application/json'
    }
    data = {
        'game_id': game_id
    }

    response = requests.patch(url, headers=headers, params=params, json=data)
    if response.status_code == 204:
        logging.info('Getting Twitch category' + "-" * 70)
        game_twitch = get_twitch_category()
        logging.warning('Stream category changed successfully: ' + game_twitch)
    else:
        logging.error('Error changing stream category:', response.text)
        logging.info('Server response:', response.json())

def get_twitch_category():
    game_twitch = True
    url = f'{BASE_TWITCH_API_URL}/channels'
    params = {
        'broadcaster_id': TWITCH_USER_ID
    }
    headers = {
        'Authorization': f'Bearer {TWITCH_TOKEN}',
        'Client-Id': TWITCH_CLIENT_ID,
        'Content-Type': 'application/json'
    }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        if data['data']:
            game_twitch=data['data'][0]['game_name']
            return game_twitch
        else:
            logging.warning('Twitch category not found')
            return None
    else:
        logging.error('Error getting stream category:', response.text)
        logging.info('Server response:', response.json())

def search_twitch_game_id(game):
    logging.info('Searching Twitch game ID' + "-" * 70)
    url = f'{BASE_TWITCH_API_URL}/search/categories'
    params = {
        'query': game,
        'first': '1'
    }
    headers = {
        'Authorization': f'Bearer {TWITCH_TOKEN}',
        'Client-Id': TWITCH_CLIENT_ID,
        'Content-Type': 'application/json'
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        if data['data']:
            return data['data'][0]['id']
        else:
            logging.warning('Game ID not found on Twitch.')
            return None
    else:
        logging.error('Error searching for the game ID on Twitch:', response.text)
        return None

@tasks.loop(seconds=10)
async def check_presence():
    global current_game
    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    if channel:
        guild = channel.guild
        if guild:
            new_game = guild.get_member(DISCORD_USER_ID).activity.name if guild.get_member(DISCORD_USER_ID).activity else None
            if new_game != current_game:
                logging.warning("Opened game/program detected: " + (new_game if new_game else "None") + "-" * 70)
                current_game = new_game
                if new_game:
                    for category, programArray in cat_exact.items():
                        if new_game in programArray:
                            game_id_twitch = search_twitch_game_id(category)
                            change_twitch_category(game_id_twitch)
                            return
                    for category, programArray in cat_contains.items():
                        for program in programArray:
                            if program in new_game:
                                game_id_twitch = search_twitch_game_id(category)
                                change_twitch_category(game_id_twitch)
                                return     
                    game_id_twitch = search_twitch_game_id(new_game)
                    change_twitch_category(game_id_twitch)
                    return 
                else:
                    logging.warning("You are not playing any game at the moment." + "-" * 70)
                    game_id_twitch = search_twitch_game_id("Just Chatting")
                    if game_id_twitch:
                        change_twitch_category(game_id_twitch)
                        get_twitch_category()
    else:
        logging.warning("Channel not found.")

@bot.event
async def on_ready():
    logging.info('Bot connected')
    check_presence.start()
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.custom, name="custom", state="https://github.com/bastianbatory/"))
bot.run(DISCORD_BOT_TOKEN) 
