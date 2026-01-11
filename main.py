import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import requests
import datetime
import random
import storage

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
            await ctx.send(f"🕵️ **Wordle No. `{date_count}` Spoiler!**\nDate: {pretty_date}\nToday's answer is: ||**{solution}**||")
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
    mention = ctx.author.mention
    # Check if the user is already in an active game
    if ctx.author.id in active_games:
        await ctx.send(f"{mention},\n❌ **You already have a game running! Finish it or just keep guessing.**")
        return
    
    # Pick a random word and initialize game state
    secret_word = random.choice(word_list)
    active_games[ctx.author.id] = {
        "word" : secret_word, 
        "history": [],                          # Stores past guesses in visual rows
        "greens": ["_", "_", "_", "_", "_"],    # Tracks known correct positions
        "yellows": set(),                       # Tracks known valid letters (use hashset to prevent dupes)
        "grays": set()                          # Tracks bad letters which are gray
    }
    await ctx.send(f"{mention}, 🎮 **New Game Started!**\nI've picked a secret 5-letter word.\nType `!guess WORD` to play!")

@bot.command()
async def guess(ctx, user_guess: str):
    mention = ctx.author.mention
    if ctx.author.id not in active_games:
        await ctx.send(f"{mention},\n**❌ You aren't playing right now! Type `!play` to start.**")
        return
    
    # Retrieve user's specific game data
    game_data = active_games[ctx.author.id]
    target_word = game_data["word"]
    history = game_data["history"]
    known_greens = game_data["greens"]
    known_yellows = game_data["yellows"]

    user_guess = user_guess.upper()

    if len(user_guess) != 5:
        await ctx.send(f"{mention}, ⚠️ Guess must be exactly 5 letters!")
        return
    if user_guess not in word_list:
        await ctx.send(f"{mention},\n❌ **{user_guess}** is not a valid word in my dictionary!")
        return
    
    # Check for a duplicate word and set it invalid
    for past_entry in history:
        if f"(`{user_guess}`)" in past_entry:
            await ctx.send(f"{mention},\n ⚠️ You already guessed **{user_guess}**! Try a different word.")
            return

    # Logic for Coloring (Green/Yellow/White)
    target_counts = {}
    for char in target_word:
        # Frequency Count: Count letter availability in the target word
        target_counts[char] = target_counts.get(char, 0) + 1 

    result = ["⬜ "] * 5 # Default state of 5 gray letters

    # Find GREEN matches perfectly
    for i in range(5):
        letter = user_guess[i]
        if letter == target_word[i]:
            result[i] = "🟩 "
            target_counts[letter] -= 1

            known_greens[i] = letter
            if letter in known_yellows:
                known_yellows.remove(letter)

    # Find YELLOW matches which are the remaining letters
    for i in range(5):
        letter = user_guess[i]
        if result[i] == "🟩 ": # Skip if we already marked it Green
            continue
            
        # Check if letter exists in the target word and you still have counts left 
        if letter in target_word and target_counts[letter] > 0:
            result[i] = "🟨 "
            target_counts[letter] -= 1

            # Update status display lists
            if letter not in known_greens:
                known_yellows.add(letter)

    # If there is no counts left, letters stay gray
    # Build the final row string
    row_emojis = "".join(result)
    full_row = f"{row_emojis} (`{user_guess}`)"
    history.append(full_row)

    # Prepare status header (shows which letter user has found so far)
    green_display = " ".join(known_greens)
    yellow_display = ", ".join(sorted(known_yellows)) if known_yellows else "None"
    status_header = f"{mention},\n💚 **Correct:** `{green_display}`\n💛 **Valid:** `{yellow_display}`\n"

    # Build Final Response & Check Win/Loss
    board_display = "\n".join(history)
    final_message = f"{status_header}\n{board_display}"
    attempts_used = len(history)
    
    # Update Invalid Letters (grays) for the !hint command
    for letter in user_guess:
        if letter not in target_word:
            game_data["grays"].add(letter)
    
    if user_guess == target_word:
        storage.update_stat(ctx.author.id, 'win') # update the win count by 1

        await ctx.send(f"{final_message}\n\n🎉 **YOU WON!** The word was **{target_word}.\n🤔 Attempts:** {attempts_used}")
        del active_games[ctx.author.id] # Clear game from memory
    elif attempts_used >= 6:
        storage.update_stat(ctx.author.id, 'loss') # update the loss count by 1

        await ctx.send(f"{final_message}\n\n💀 **GAME OVER!** You ran out of guesses.\nThe word was: ||**{target_word}**||")
        del active_games[ctx.author.id] # Clear game from memory
    else:
        remaining = 6 - attempts_used
        word = "guess" if remaining == 1 else "guesses"
        await ctx.send(f"{final_message}\n\n**{remaining}** {word} remaining.")

# UTILITY COMMANDS
@bot.command()
async def hint(ctx):
    mention = ctx.author.mention

    if ctx.author.id not in active_games: # Make sure the user is actually playing a game
        await ctx.send(f"{mention},\n**❌ You aren't playing right now! Type `!play` to start.**")
        return
    
    # Get the current game constraints from memory
    game_data = active_games[ctx.author.id]
    known_greens = game_data["greens"]
    known_yellows = game_data["yellows"]
    known_grays = game_data["grays"]

    await ctx.send("🧠 **Thinking...** scanning dictionary for matches...")

    possible_matches = []

    for word in word_list: # Iterate through every word in the dictionary 
        # Constraint 1: Correct Green Positions: word must have exact same letter in exact spot to be green
        match_greens = True
        for i in range(5):
            # if a green letter exists at [i], the hint word MUST match this
            if known_greens[i] != "_" and known_greens[i] != word[i]: 
                match_greens = False
                break
        if not match_greens:
            continue # Skip this word since it has a conflict with green clue
        
        # Constraint 2: Yellow Letters Exists: word must contain all yellow letters somewhere
        match_yellows = True
        for letter in known_yellows:
            if letter not in word:
                match_yellows = False
                break
        if not match_yellows:
            continue # Skip the word since its missing a important yellow letter
        
        # Constraint 3: Gray Letters INVALID: word must not contain any gray letters 
        match_grays = True
        for letter in known_grays: 
            if letter in word: # Rule out a letter if its not in the Green/Yellow list
                match_grays = False
                break
        if not match_grays:
            continue # Skip this word it contains a forbidden gray letter

        possible_matches.append(word)

    if not possible_matches:
        await ctx.send(f"{mention}\n❌ I couldn't find ANY words that fit your current clues! (Did you make a mistake?)")
    else:
        random.shuffle(possible_matches) # Shuffle results for better matches 

        suggestions = possible_matches[:10] # Only show the top 10 best matches 
        result_str = ", ".join(suggestions)
        
        await ctx.send(f"{mention},\n💡 **Hints found:** {len(possible_matches)}\nHere are 10 options:\n`{result_str}`")

@bot.command()
async def surrender(ctx):
    mention = ctx.author.mention

    if ctx.author.id not in active_games: # Check if the user is actually playing
        await ctx.send(f"{mention},\n**❌ You aren't playing right now! Type `!play` to start.**")
        return

    # Retrieve the secret word so you can show the user
    game_data = active_games[ctx.author.id]
    target_word = game_data["word"]

    # This counts as a loss for giving up
    storage.update_stat(ctx.author.id, 'loss')

    # End the game
    await ctx.send(f"{mention}\n 🏳️ **You surrendered.**\nThe secret word was: ||**{target_word}**||\n\n📉 This has been recorded as a **loss**.")
    del active_games[ctx.author.id]

@bot.command()
async def stats(ctx):
    data = storage.get_stats(ctx.author.id) # use Discord ID to retrieve data from the specific user running !stats

    wins = data["wins"]
    losses = data["losses"]
    streak = data["streak"]
    max_streak = data["max_streak"]

    prev_win_rate = data.get("prev_win_rate", 0)

    total = wins + losses
    win_rate = round((wins / total) * 100, 1) if total > 0 else 0 # calculation for win rate percentage

    if win_rate > prev_win_rate:
        trend = "📈"
    elif win_rate < prev_win_rate:
        trend = "📉"
    else:
        trend = "🆗"

    embed = discord.Embed(
        title = f"📊 Stats for {ctx.author.display_name}",
        description = "Here are a list of your stats for Brain Wordle",
        color=0xffd700
    )
    embed.set_thumbnail(url=ctx.author.display_avatar.url) # Added a image section for stats

    embed.add_field( name = "Wins", value = str(wins), inline = True )
    embed.add_field( name = "Loss", value = str(losses), inline = True)
    embed.add_field( name = "Games", value=str(total), inline=True)
    embed.add_field( name = "Win Rate", value = f"{win_rate}% {trend}", inline = True )
    embed.add_field( name = "Streak", value = f"🔥 {streak}", inline=True )
    embed.add_field( name = "Best Streak", value = f"🏆 {max_streak}", inline=True)

    await ctx.send(embed=embed)

# HELP COMMAND (shows a list of commands you can use in discord chat)
@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title = "🤖 Brain Wordle Bot Help", description = "Here are the commands you can use:", color = 0x92ed8a
    )
    embed.add_field(
        name="🕵️ !nyt", value = "Reveals today's official NYT Wordle answer (Spoiler tagged!)", inline = False
    )
    embed.add_field(
        name = "🎮 !play", value = "Starts a new unlimited Wordle game just for you.", inline = False
    )
    embed.add_field(
        name = "🔤 !guess [WORD]", value = "Make a guess in your active game. (Example: `!guess APPLE`)", inline = False
    )
    embed.add_field(
        name = "🤫 !hint", value = "Reveals BEST possible options to guide you in Wordle", inline = False
    )
    embed.add_field(
        name = "📈 !stats", value = "View your win/loss record", inline = False
    )
    embed.add_field(
        name = "❌ !surrender", value = "Surrender and view the correct word immediately", inline = False
    )

    embed.set_footer(text="Bot created by TazCtrl")
    await ctx.send(embed=embed)

# EXECUTE THE BOT
bot.run(token, log_handler=handler, log_level=logging.DEBUG)