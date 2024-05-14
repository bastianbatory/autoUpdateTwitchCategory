import discord
from discord.ext import commands, tasks
import asyncio
import requests
import json

# Load configuration from config.json file
with open('config.json') as f:
    config = json.load(f)

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


# Function to print the current game to the console every 5 seconds
async def print_current_game():
    while True:
        await asyncio.sleep(5)
        if current_game:
            print(f"Current game: {current_game}")
        else:
            print("You are not playing any game at the moment.")

# Function to change the stream category on Twitch
def change_twitch_category(game_id):
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
    print('Request to the server:')
    print('PATCH', url)
    print('Parameters:', params)
    print('Data:', data)
    print('Headers:', headers)
    # Send the HTTP request
    response = requests.patch(url, headers=headers, params=params, json=data)
    # Check the response
    if response.status_code == 204:
        print('Stream category changed successfully.')
    else:
        print('Error changing stream category:', response.text)
        print('Server response:', response.json())

# Function to search for the game ID on Twitch
def search_twitch_game_id(game):
    # Twitch API URL to search for the game ID
    url = f'{BASE_TWITCH_API_URL}/search/categories'
    # Request parameters
    params = {
        'query': game
    }
    # Request headers with the access token
    headers = {
        'Authorization': f'Bearer {TWITCH_TOKEN}',
        'Client-Id': TWITCH_CLIENT_ID,
        'Content-Type': 'application/json',
        'first': '2'
    }
    # Print the complete request before sending it
    print('Request to the server:')
    print('GET', url)
    print('Parameters:', params)
    print('Headers:', headers)
    # Send the HTTP request
    response = requests.get(url, headers=headers, params=params)
    # Check the response
    if response.status_code == 200:
        data = response.json()
        if data['data']:
            return data['data'][0]['id']
        else:
            print('Game ID not found on Twitch.')
            return None
    else:
        print('Error searching for the game ID on Twitch:', response.text)
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
                current_game = new_game
                # If the game is not None (i.e., if a game is being played), search for the game ID on Twitch
                if new_game and new_game != "Spotify" and new_game != "Twitch":
                    game_id_twitch = search_twitch_game_id(new_game)
                    # If the game ID is found on Twitch, change the stream category
                    if game_id_twitch:
                        change_twitch_category(game_id_twitch)
                else:
                    # If no game is being played, set "Just Chatting" as the current game
                    game_id_twitch = search_twitch_game_id("Just Chatting")
                    if game_id_twitch:
                        change_twitch_category(game_id_twitch)
    else:
        print("Channel not found.")

# Event triggered when the bot connects to Discord
@bot.event
async def on_ready():
    print('Bot connected')
    # Start the task to check presence at regular intervals
    check_presence.start()
    # Start the task to print the current game to the console every 5 seconds
    bot.loop.create_task(print_current_game())

# Run the bot
bot.run(DISCORD_BOT_TOKEN)  # Bot access token
