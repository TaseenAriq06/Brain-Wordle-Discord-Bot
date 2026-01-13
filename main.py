import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

# Setup Logging
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

# Setup Bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user.name}")
    print("------")
    
    await bot.change_presence(activity=discord.Game(name="Brain Wordle 🧠 | !help"))
    
    # Load the Cogs
    initial_extensions = ['cogs.gameplay', 'cogs.utility']
    
    for extension in initial_extensions:
        try:
            await bot.load_extension(extension)
            print(f"📂 Loaded extension: {extension}")
        except Exception as e:
            print(f"❌ Failed to load extension {extension}: {e}")

bot.run(token, log_handler=handler)