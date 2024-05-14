# Auto Update Twitch Category Discord Bot

This Discord bot takes your current game from Discord and sets Twitch category automatically

## Configuration

### Installation

1. Add the repository to Visual Studio Code or download and add the project folder.
2. Install Python from [python.org](https://www.python.org).
3. Install dependencies by running the following command in your terminal:

   ```bash
   pip install -r requirements.txt
   ```
   
### Discord Configuration

1. Create an application on Discord from Discord Developer Portal.
2. Go to the Bot section and enable all Privileged Gateway Intents. Reset the Token and copy it; this will be your DISCORD_BOT_TOKEN.
3. Go to the OAuth2 section, select Bot, and choose the necessary permissions.
4. Copy the generated URL and open it in your browser to authorize the bot to join your Discord channel.
5. Go to Discord, select your profile, and copy your User ID; this will be your DISCORD_USER_ID.
6. Right-click on any channel you have permissions to and copy the channel ID; this will be your DISCORD_CHANNEL_ID.


### Twitch Configuration

1. Go to Twitch Developer Console and create an application. Copy the Client ID; this will be your TWITCH_CLIENT_ID.
2. Open this link in your browser.
3. After authorizing, copy the access_token from the redirected URL; this will be your TWITCH_TOKEN.
4. Visit [Streamweasels](https://www.streamweasels.com/tools/convert-twitch-username-to-user-id/) to get your user ID from your Twitch username; this will be your TWITCH_USER_ID.


### Edit config.json

Edit the config.json file with the copied values:

   ```json
{
    "DISCORD_CHANNEL_ID": "DISCORD_CHANNEL_ID",
    "DISCORD_USER_ID": "DISCORD_USER_ID",
    "TWITCH_USER_ID": "TWITCH_USER_ID",
    "TWITCH_TOKEN": "TWITCH_TOKEN",
    "TWITCH_CLIENT_ID": "TWITCH_CLIENT_ID",
    "DISCORD_BOT_TOKEN": "DISCORD_BOT_TOKEN"
}
```

### Running the Bot

To run the bot, simply execute the following command:

```bash

python bot.py

```

## Usage
Once the bot is running, Twitch will automatically change the game category you are playing. If you want to add a game that has not been detected, add it to the game configurations in Discord.

