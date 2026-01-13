from discord.ext import commands
import random
import storage
import random
import discord

class HintView(discord.ui.View):
    def __init__(self, cog, ctx):
        super().__init__(timeout=None) # Hint button will never expire until bot restarts
        self.cog = cog                 # Store the Gameplay cog so we can call the hint command
        self.ctx = ctx                 # Store the context so we know whos playing

    @discord.ui.button(label="💡 Hint", style=discord.ButtonStyle.blurple)
    async def hint_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id: # This verifies if the right person is clicking the hint button
            await interaction.response.send_message("❌ This isn't your game! Type `!play` to start!", ephemeral=True)
            return
        
        await interaction.response.defer() # Acknowledge the user clicking the button
        await self.cog.hint(self.ctx)      # Call the existing hint logic from the !hint command

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

            view = HintView(self, ctx)           # Create the view for the user to see the hint button per guess
            await ctx.send(f"{final_message}\n\n**{remaining}** {word} remaining.", view=view)

    # HINT COMMAND (No longer a command but uses logic for hint button per guess)
    # @commands.command()
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

    def __init__(self, bot):
            self.bot = bot
            self.active_games = {}
            self.word_list = []
            self.load_words()
            self.scramble_games = {}

    # SCRAMBLE command
    @commands.command()
    async def scramble(self, ctx):
        mention = ctx.author.mention
        # 1. Check if user is already playing a scramble game
        if ctx.author.id in self.scramble_games:
            await ctx.send(f"{mention}, You are already playing a scramble game")
            return
        # 2. Pick a random word from self.
        target = random.choice(self.word_list)
        rand_attempts = random.randint(3,10)
        # 3. Shuffle the letters (Turn to list -> shuffle -> join)
        char_list = list(target)
        random.shuffle(char_list)
        shuffled_word = "".join(char_list)

        self.scramble_games[ctx.author.id] = {
            "word" : target,
            "attempts" : rand_attempts,
            "history" : []
        }
        await ctx.send(f"{mention}, 🌪️ **Unscramble this:** `{shuffled_word}`\nType `!unscramble [WORD]` to solve it!\nYou have **{rand_attempts}** attempts ONLY!")

    # UNSCRAMBLE command
    @commands.command()
    async def unscramble(self, ctx, guess: str):
        mention = ctx.author.mention
        guess = guess.upper()
        # 1. Check if user is playing
        if ctx.author.id not in self.scramble_games:
            await ctx.send(f"{mention}, You are not playing! Type `!scramble` to start!")
            return
        # 2. Check if guess == the saved word (make sure both are .upper())
        game_data = self.scramble_games[ctx.author.id]
        correct_answer = game_data["word"]
        attempts_left = game_data["attempts"]
        hist = game_data["history"]

        if len(guess) != 5:
            await ctx.send(f"{mention}, ⚠️ Guess must be exactly 5 letters!")
            return
        
        # Array to hold all invalid letters
        invalid_letters = []
        for char in guess.upper():
            # Check if char is wrong AND if we haven't listed it already
            if char not in correct_answer and char not in invalid_letters:
                invalid_letters.append(char)
        
        # If the list is not empty, it means we found bad letters
        if invalid_letters:
            bad_display = ", ".join(invalid_letters)
            await ctx.send(f"{mention}, ⚠️ These letters are not in the word: **{bad_display}** (No attempt lost)")
            return

        # Checks if user has already used the same word to unscramble
        if guess in hist:
            await ctx.send(f"{mention},\n ⚠️ You already guessed **{guess}**! Try a different word.")
            return
        
        hist.append(guess)

        if guess == correct_answer:
            await ctx.send(f"{mention}, Nice job! The correct answer was **{correct_answer}**")
            del self.scramble_games[ctx.author.id]
        else:
            attempts_left -= 1

            if attempts_left == 0:
                await ctx.send(f"{mention},\n💀 **Game Over!** You ran out of attempts.\nThe word was: **{correct_answer}**")
                del self.scramble_games[ctx.author.id]
            else:
                self.scramble_games[ctx.author.id]["attempts"] = attempts_left
                await ctx.send(f"{mention}\n❌ **Wrong!** Try again. ({attempts_left} attempts left)")

async def setup(bot):
    await bot.add_cog(Gameplay(bot))
