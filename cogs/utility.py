import discord
from discord.ext import commands
import storage
import requests
import datetime

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    # NYT Command
    @commands.command() 
    async def nyt(self, ctx):
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

    # STATS Command
    @commands.command()
    async def stats(self, ctx):
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

        embed.add_field(name = "Wins", value = str(wins), inline = True)
        embed.add_field(name = "Loss", value = str(losses), inline = True)
        embed.add_field(name = "Games", value=str(total), inline=True)
        embed.add_field(name = "Win Rate", value = f"{win_rate}% {trend}", inline = True)
        embed.add_field(name = "Streak", value = f"🔥 {streak}", inline=True)
        embed.add_field(name = "Best Streak", value = f"🏆 {max_streak}", inline=True)

        await ctx.send(embed=embed)

    # HELP Command (shows a list of commands you can use in discord chat)
    @commands.command()
    async def help(self, ctx):
        embed = discord.Embed(
            title = "🤖 Brain Wordle Bot Help", description = "Here are the commands you can use:", color = 0x92ed8a
        )
        embed.add_field(name = "🕵️ !nyt", value = "Reveals today's official NYT Wordle answer (Spoiler tagged!)", inline = False)
        embed.add_field(name = "🎮 !play", value = "Starts a new unlimited Wordle game just for you.", inline = False)
        embed.add_field(name = "🔤 !guess [WORD]", value = "Make a guess in your active game. (Example: `!guess APPLE`)", inline = False)
        embed.add_field(name = "🤫 !hint", value = "Reveals BEST possible options to guide you in Wordle", inline = False)
        embed.add_field(name = "📈 !stats", value = "View your win/loss record", inline = False)
        embed.add_field(name = "❌ !surrender", value = "Surrender and view the correct word immediately", inline = False)
        embed.add_field(name = "🌪️ !scramble/!unscramble", value = "Bot shuffles a word and YOU have to unscramble the word", inline = False)
        embed.set_footer(text="Bot created by TazCtrl")
        await ctx.send(embed=embed)
        
async def setup(bot):
    await bot.add_cog(Utility(bot))