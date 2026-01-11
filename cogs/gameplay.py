from discord.ext import commands
import random
import storage

class Gameplay(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_games = {}
        self.word_list = []
        self.load_words()

    def load_words(self):
        try:
            with open('words.txt', 'r') as f:
                content = f.read().split()
                self.word_list = [word.upper() for word in content if len(word) == 5]
            print(f"✅ Cog Loaded: {len(self.word_list)} words.")
        except:
            print("❌ Error: words.txt not found!")
            self.word_list = ["ERROR"]

    # PLAY command
    @commands.command()
    async def play(self, ctx):
        mention = ctx.author.mention
        # Check if the user is already in an active game
        if ctx.author.id in self.active_games:
            await ctx.send(f"{mention},\n❌ **You already have a game running! Finish it or just keep guessing.**")
            return
    
        # Pick a random word and initialize game state
        secret_word = random.choice(self.word_list)
        self.active_games[ctx.author.id] = {
            "word" : secret_word, 
            "history": [],                                       # Stores past guesses in visual rows
            "greens": ["_", "_", "_", "_", "_"],                 # Tracks known correct positions
            "yellows": set(),                                    # Tracks known valid letters (use hashset to prevent dupes)
            "grays": set(),                                      # Tracks bad letters which are gray
            "bad_positions": [set(), set(), set(), set(), set()] # List of 5 sets to hold specific index values for each letter
        }
        await ctx.send(f"{mention}, 🎮 **New Game Started!**\nI've picked a secret 5-letter word.\nType `!guess WORD` to play!")

    # GUESS Command
    @commands.command()
    async def guess(self, ctx, user_guess: str):
        mention = ctx.author.mention
        if ctx.author.id not in self.active_games:
            await ctx.send(f"{mention},\n**❌ You aren't playing right now! Type `!play` to start.**")
            return
    
        # Retrieve user's specific game data
        game_data = self.active_games[ctx.author.id]
        target_word = game_data["word"]
        history = game_data["history"]
        known_greens = game_data["greens"]
        known_yellows = game_data["yellows"]

        user_guess = user_guess.upper()

        if len(user_guess) != 5:
            await ctx.send(f"{mention}, ⚠️ Guess must be exactly 5 letters!")
            return
        if user_guess not in self.word_list:
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
                game_data["bad_positions"][i].add(letter)

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
            del self.active_games[ctx.author.id] # Clear game from memory
        elif attempts_used >= 6:
            storage.update_stat(ctx.author.id, 'loss') # update the loss count by 1

            await ctx.send(f"{final_message}\n\n💀 **GAME OVER!** You ran out of guesses.\nThe word was: ||**{target_word}**||")
            del self.active_games[ctx.author.id] # Clear game from memory
        else:
            remaining = 6 - attempts_used
            word = "guess" if remaining == 1 else "guesses"
            await ctx.send(f"{final_message}\n\n**{remaining}** {word} remaining.")

    # HINT COMMAND
    @commands.command()
    async def hint(self, ctx):
        mention = ctx.author.mention

        if ctx.author.id not in self.active_games: # Make sure the user is actually playing a game
            await ctx.send(f"{mention},\n**❌ You aren't playing right now! Type `!play` to start.**")
            return
    
        # Get the current game constraints from memory
        game_data = self.active_games[ctx.author.id]
        known_greens = game_data["greens"]
        known_yellows = game_data["yellows"]
        known_grays = game_data["grays"]
        history = game_data["history"]
        bad_positions = game_data["bad_positions"]

        await ctx.send("🧠 **Thinking...** scanning dictionary for matches...")

        possible_matches = []

        for word in self.word_list: # Iterate through every word in the dictionary 
            already_guessed = False
            for entry in history:
                if f"(`{word}`)" in entry:        # Makes sure the !hint does not suggest a word you tried already
                    already_guessed = True
                    break
            if already_guessed:
                continue

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

            # Constraint 4: If a yellow letter is at a specific spot, do not suggest hints that contain yellow letters in the same spot
            match_positions = True      
            for i in range(5):
                if word[i] in bad_positions[i]:
                    match_positions = False
                    break
            if not match_positions:
                continue

            possible_matches.append(word)

        if not possible_matches:
            await ctx.send(f"{mention}\n❌ I couldn't find ANY words that fit your current clues! (Did you make a mistake?)")
        else:
            random.shuffle(possible_matches) # Shuffle results for better matches 

            suggestions = possible_matches[:10] # Only show the top 10 best matches 
            shown_count = len(suggestions)
            result_str = ", ".join(suggestions)
            
            await ctx.send(f"{mention},\n💡 **Hints found:** {len(possible_matches)}\nHere are **{shown_count}** options:\n`{result_str}`")
    
    # SURRENDER COMMAND
    @commands.command()
    async def surrender(self, ctx):
        mention = ctx.author.mention

        if ctx.author.id not in self.active_games: # Check if the user is actually playing
            await ctx.send(f"{mention},\n**❌ You aren't playing right now! Type `!play` to start.**")
            return

        # Retrieve the secret word so you can show the user
        game_data = self.active_games[ctx.author.id]
        target_word = game_data["word"]

        # This counts as a loss for giving up
        storage.update_stat(ctx.author.id, 'loss')

        # End the game
        await ctx.send(f"{mention}\n 🏳️ **You surrendered.**\nThe secret word was: ||**{target_word}**||\n\n📉 This has been recorded as a **loss**.")
        del self.active_games[ctx.author.id]

async def setup(bot):
    await bot.add_cog(Gameplay(bot))
