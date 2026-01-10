import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import requests
import datetime
import random

# Load environmental variables from the .env file to keep token safe
load_dotenv()
token = os.getenv('DISCORD_TOKEN')

# Set up logging to track errors in discord.log
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default() # Configure Intents to tell Discord what the bot is allowed to see
intents.message_content = True
intents.members = True

# Initialize bot with the command prefix "!"
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# Event Listener
@bot.event
async def on_ready():
    # Outputs a message in the terminal to show bot is active
    print(f"{bot.user.name} is now ACTIVE")
    await bot.change_presence(activity=discord.Game(name="Type !help for the list of commands."))

@bot.event
async def on_member_join(member):
    # Sends a private DM to the new user who joins the server
    await member.send(f"Welcome to the server {member.name}") 

@bot.event
async def on_message(message):
    # Prevents bot from replying to itself to avoid infinite loops
    if message.author == bot.user:
        return
    await bot.process_commands(message)

# NYT API Command
@bot.command()
async def nyt(ctx):
    # Get today's date formatted for the API URL (YYYY-MM-DD)
    date_string = datetime.date.today().strftime("%Y-%m-%d")
    url = f"https://www.nytimes.com/svc/wordle/v2/{date_string}.json"

    today = datetime.date.today()

    pretty_date = f"{today.strftime('%B')} {today.day}, {today.year}"

    try:
        # Mimic a real browser to avoid being blocked by NYT
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            solution = data['solution'].upper()
            date_count = data['days_since_launch']

            # Send the answer hidden behind a spoiler tag
            await ctx.send(f"🕵️ **Wordle No. {date_count} Spoiler!**\nDate: {pretty_date}\nToday's answer is: ||**{solution}**||")
        else:
            await ctx.send("❌ Error: Couldn't find today's Wordle. NYT might be down!")
    except Exception as e:
        await ctx.send(f"⚠️ Something went wrong: {e}")

# Dictionary to store active games (KEY:VALUE):(USER ID: Game Data)
active_games = {}
word_list = []

# Load dictionary words from file
try:
    with open('words.txt', 'r') as f:
        content = f.read().split()
        # List to keep only valid 5 letter-words (already set in words.txt)
        word_list = [word.upper() for word in content if len(word) == 5]
    
    print(f"✅ Loaded {len(word_list)} words from words.txt")
except:
    print("❌ Error: words.txt not found! Using backup list.")
    word_list = ["ERROR", "DEBUG", "TESTS"]

# GAME COMMANDS
@bot.command()
async def play(ctx):
    # Check if the user is already in an active game
    if ctx.author.id in active_games:
        await ctx.send("❌ You already have a game running! Finish it or just keep guessing.")
        return
    
    # Pick a random word and initialize game state
    secret_word = random.choice(word_list)
    active_games[ctx.author.id] = {
        "word" : secret_word, 
        "history": [],                          # Stores past guesses in visual rows
        "greens": ["_", "_", "_", "_", "_"],    # Tracks known correct positions
        "yellows": set()                        # Tracks known valid letters (use hashset to prevent dupes)
    }
    await ctx.send(f"🎮 **New Game Started!**\nI've picked a secret 5-letter word.\nType `!guess WORD` to play!")

@bot.command()
async def guess(ctx, user_guess: str):
    if ctx.author.id not in active_games:
        await ctx.send("❌ You aren't playing right now! Type `!play` to start.")
        return
    
    # Retrieve user's specific game data
    game_data = active_games[ctx.author.id]
    target_word = game_data["word"]
    history = game_data["history"]
    known_greens = game_data["greens"]
    known_yellows = game_data["yellows"]

    user_guess = user_guess.upper()

    if len(user_guess) != 5:
        await ctx.send("⚠️ Guess must be exactly 5 letters!")
        return
    if user_guess not in word_list:
        await ctx.send(f"❌ **{user_guess}** is not a valid word in my dictionary!")
        return
    
    # Check for a duplicate word and set it invalid
    for past_entry in history:
        if f"(`{user_guess}`)" in past_entry:
            await ctx.send(f"⚠️ You already guessed **{user_guess}**! Try a different word.")
            return

    # Logic for Coloring (Green/Yellow/White)
    row_emojis = ""
    for i in range (5):
        letter = user_guess[i]

        # Case 1: Green for correct letter, correct spot
        if user_guess[i] == target_word[i]:
            row_emojis += "🟩 "
            known_greens[i] = letter

            # If letter is found in green, remove from yellow list
            if letter in known_yellows:
                known_yellows.remove(letter)

        # Case 2: Yellow for correct letter, wrong placement
        elif user_guess[i] in target_word:
            row_emojis += "🟨 "
            
            # Only add to yellows if we haven't found it in the correct spot
            if letter not in known_greens:
                known_yellows.add(letter)
        # Case 3: Letter is not in the word at all
        else:
            row_emojis += "⬜ "
    
    # Format the row to show emojis + the actual word
    full_row = f"{row_emojis}  (`{user_guess}`)"
    history.append(full_row)

    # Prepare status header (shows which letter user has found so far)
    green_display = " ".join(known_greens)
    yellow_display = ", ".join(sorted(known_yellows)) if known_yellows else "None"
    status_header = f"💚 **Correct:** `{green_display}`\n💛 **Valid:** `{yellow_display}`\n"

    # Build Final Response & Check Win/Loss
    board_display = "\n".join(history)
    final_message = f"{status_header}\n{board_display}"
    attempts_used = len(history)
    
    if user_guess == target_word:
        await ctx.send(f"{final_message}\n\n🎉 **YOU WON!** The word was **{target_word}**.")
        del active_games[ctx.author.id] # Clear game from memory
    elif attempts_used >= 6:
        await ctx.send(f"{final_message}\n\n💀 **GAME OVER!** You ran out of guesses.\nThe word was: ||**{target_word}**||")
        del active_games[ctx.author.id] # Clear game from memory
    else:
        await ctx.send(f"{final_message}\n\n**{6 - attempts_used}** guesses remaining.")

# UTILITY COMMANDS
@bot.command()
async def unscramble(ctx, user_word: str):
    user_word = user_word.upper()

    if len(user_word) != 5:
        await ctx.send("⚠️ Please provide exactly 5 letters!")
        return
    # Sort the user's letters to compare against sorted dictionary words
    target_word = sorted(user_word)
    found_words = []

    for word in word_list:
        if sorted(word) == target_word:
            found_words.append(word)
    
    if found_words:
        result_string = ", ".join(found_words)
        await ctx.send(f"🧩 **Unscrambled options for {user_word}:**\n`{result_string}`")
    else:
        await ctx.send(f"❌ No valid words found using the letters in **{user_word}**.")

# HELP COMMAND (shows a list of commands you can use in discord chat)
@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title = "🤖 WordleMaster Bot Help",
        description = "Here are the commands you can use:",
        color = 0x92ed8a
    )

    embed.add_field(
        name="🕵️ !nyt",
        value = "Reveals today's official NYT Wordle answer (Spoiler tagged!)",
        inline = False
    )
    embed.add_field(
        name = "🎮 !play",
        value = "Starts a new unlimited Wordle game just for you.",
        inline = False
    )
    embed.add_field(
        name = "🔤 !guess [WORD]",
        value = "Make a guess in your active game. (Example: `!guess APPLE`)",
        inline = False
    )
    embed.add_field(
        name = "🧩 !unscramble [WORD]",
        value = "Unscramble a word for a better guessed attempt in Wordle",
        inline = False
    )

    embed.set_footer(text="Bot created by TazCtrl")
    await ctx.send(embed=embed)

# EXECUTE THE BOT
bot.run(token, log_handler=handler, log_level=logging.DEBUG)