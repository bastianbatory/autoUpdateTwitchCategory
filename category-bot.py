import discord
from discord.ext import commands, tasks
import asyncio
import requests
import json
import logging
import colorlog


# Crear un manejador de consola con colores usando colorlog
console_handler = colorlog.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Definir el formato del log con colores específicos y un tabulador entre la hora y el nivel de registro
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

# Obtener el logger root y añadirle el manejador de consola con colores
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
root_logger.addHandler(console_handler)


# Load configuration from config.json file
with open('config.json') as f:
    config = json.load(f)

# Load manual categories from manual-cat.json file
with open('cat-contains.json') as f:
    cat_contains = json.load(f)

with open('cat-exact.json') as f:
    cat_exact = json.load(f)

# Bot intents
intents = discord.Intents.default()
intents.presences = True
intents.members = True

# Configure the bot with intents
bot = commands.Bot(command_prefix='!', intents=intents)

# Extract tokens and IDs from the configuration file
DISCORD_CHANNEL_ID = int(config["DISCORD_CHANNEL_ID"])
DISCORD_USER_ID = int(config["DISCORD_USER_ID"])
DISCORD_BOT_TOKEN = config["DISCORD_BOT_TOKEN"]
TWITCH_USER_ID = config["TWITCH_USER_ID"]
TWITCH_TOKEN = config["TWITCH_TOKEN"]
TWITCH_CLIENT_ID = config["TWITCH_CLIENT_ID"]

# Base URL of the Twitch API to change the stream category
BASE_TWITCH_API_URL = 'https://api.twitch.tv/helix'

# Variable to store the current game
current_game = None
previous_game = None


# Function to change the stream category on Twitch
def change_twitch_category(game_id):
    logging.info('Changing Twitch category' + "-" * 70)
    # Twitch API URL to change the stream category
    url = f'{BASE_TWITCH_API_URL}/channels'
    # Request parameters with the broadcaster ID
    params = {
        'broadcaster_id': TWITCH_USER_ID
    }
    # Request headers with the access token
    headers = {
        'Authorization': f'Bearer {TWITCH_TOKEN}',
        'Client-Id': TWITCH_CLIENT_ID,
        'Content-Type': 'application/json'
    }
    # Data to change the stream category
    data = {
        'game_id': game_id
    }
    # Print the complete request before sending it

    # Send the HTTP request
    response = requests.patch(url, headers=headers, params=params, json=data)
    # Check the response
    if response.status_code == 204:
        logging.info('Getting Twitch category' + "-" * 70)
        game_twitch = get_twitch_category()
        logging.info('Stream category changed successfully: ' + game_twitch)
    else:
        logging.warning('Error changing stream category:', response.text)
        logging.debug('Server response:', response.json())

def get_twitch_category():
    # Twitch API URL to change the stream category
    game_twitch = True
    url = f'{BASE_TWITCH_API_URL}/channels'
    # Request parameters with the broadcaster ID
    params = {
        'broadcaster_id': TWITCH_USER_ID
    }
    # Request headers with the access token
    headers = {
        'Authorization': f'Bearer {TWITCH_TOKEN}',
        'Client-Id': TWITCH_CLIENT_ID,
        'Content-Type': 'application/json'
    }

    # Print the complete request before sending it
    # Send the HTTP request
    response = requests.get(url, headers=headers, params=params)
    # Check the response
    if response.status_code == 200:
        data = response.json()
        if data['data']:
            game_twitch=data['data'][0]['game_name']
            return game_twitch
        else:
            logging.warning('Twitch category not found')
            return None
    else:
        logging.warning('Error getting stream category:', response.text)
        logging.debug('Server response:', response.json())

# Function to search for the game ID on Twitch
def search_twitch_game_id(game):
    # Twitch API URL to search for the game ID   
    logging.info('Searching Twitch game ID' + "-" * 70)
    url = f'{BASE_TWITCH_API_URL}/search/categories'
    # Request parameters
    params = {
        'query': game,
        'first': '1'
    }
    # Request headers with the access token
    headers = {
        'Authorization': f'Bearer {TWITCH_TOKEN}',
        'Client-Id': TWITCH_CLIENT_ID,
        'Content-Type': 'application/json'
    }
    # Send the HTTP request
    response = requests.get(url, headers=headers, params=params)
    # Check the response
    if response.status_code == 200:
        data = response.json()
        if data['data']:
            return data['data'][0]['id']
        else:
            logging.warning('Game ID not found on Twitch.')
            return None
    else:
        logging.warning('Error searching for the game ID on Twitch:', response.text)
        return None

# Function to check presence at regular intervals
@tasks.loop(seconds=10)
async def check_presence():
    global current_game
    
    # Get the Guild object corresponding to the channel
    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    if channel:
        guild = channel.guild
        if guild:
            # Get the current game of the bot owner in the server
            new_game = guild.get_member(DISCORD_USER_ID).activity.name if guild.get_member(DISCORD_USER_ID).activity else None
            # If the current game is different from the new game, update the current game variable
            if new_game != current_game:
                logging.info("Opened game/program detected: " + (new_game if new_game else "None") + "-" * 70)
                current_game = new_game
                # If the game is not None (i.e., if a game is being played), search for the game ID on Twitch
                if new_game:
                    for category, programArray in cat_exact.items():
                        if new_game in programArray:
                            game_id_twitch = search_twitch_game_id(category)
                            change_twitch_category(game_id_twitch)
                            return
                    for category, programArray in cat_contains.items():
                        for programa in programArray:
                            if programa in new_game:
                                game_id_twitch = search_twitch_game_id(category)
                                change_twitch_category(game_id_twitch)
                                return     
                    game_id_twitch = search_twitch_game_id(new_game)
                    change_twitch_category(game_id_twitch)
                    return 
                else:
                    # If no game is being played, set "Just Chatting" as the current game
                    logging.info("You are not playing any game at the moment." + "-" * 70)
                    game_id_twitch = search_twitch_game_id("Just Chatting")
                    if game_id_twitch:
                        change_twitch_category(game_id_twitch)
                        get_twitch_category()
    else:
        logging.warning("Channel not found.")

# Event triggered when the bot connects to Discord
@bot.event
async def on_ready():
    logging.info('Bot connected')
    # Start the task to check presence at regular intervals
    check_presence.start()
    # Start the task to print the current game to the console every 5 seconds
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.custom, name="custom", state="https://github.com/bastianbatory/"))
# Run the bot
bot.run(DISCORD_BOT_TOKEN)  # Bot access token
