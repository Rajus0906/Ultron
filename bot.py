import discord
from discord.ext import commands
import feedparser
import os
from dotenv import load_dotenv
from google import genai

# Fix 1: Add parentheses so load_dotenv actually executes
load_dotenv()

# Fix 2: Pass the API key correctly into the client after loading environment variables
api_key = os.getenv("GEMINI_API_KEY")
ai_client = genai.Client(api_key=api_key)

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)
        
    async def setup_hook(self):
        await self.tree.sync()
        print("Slash commands synced globally")
        
    async def on_ready(self):
        print(f"{self.user} is now online")

bot = MyBot()

@bot.tree.command(name="ping", description="Check the bot's latency")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"Ping is {latency}ms")
    
@bot.tree.command(name="patch", description="Fetch and AI-summarize the latest game patch notes")
async def patch(interaction: discord.Interaction, game: str):
    await interaction.response.defer()
    
    feeds = {
        "valorant": "https://playvalorant.com/en-us/news/rss/",
        "cs2": "https://blog.counter-strike.net/index.php/feed/",
    }
    
    game_key = game.lower()
    if game_key not in feeds:
        await interaction.followup.send(f"Sorry, I don't have an RSS feed saved for **{game}**. Try 'valorant' or 'cs2'.")
        return
        
    news_feed = feedparser.parse(feeds[game_key])
    if not news_feed.entries:
        await interaction.followup.send(f"Could not fetch updates for {game} at this time.")
        return
        
    latest = news_feed.entries[0]
    raw_text = latest.get('summary', latest.get('title', ''))
    
    prompt = f"""
    You are an expert gaming assistant. Summarize the following game update/patch notes into a concise, punchy Discord format. 
    Include:
    - Major changes
    - Buffs / Nerfs (if applicable)
    
    Keep it under 800 characters so it fits nicely inside a Discord message.
    
    Patch Notes text:
    {raw_text}
    """
    
    try:
        response = await ai_client.aio.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        ai_summary = response.text
    except Exception as e:
        ai_summary = "Could not generate AI summary, but you can read the full article below."

    embed = discord.Embed(
        title=latest.title,
        url=latest.link,
        color=discord.Color.brand_green()
    )
    embed.description = ai_summary
    embed.set_footer(text=f"AI Summary for {game.capitalize()} • Source: Official RSS")
    
    await interaction.followup.send(embed=embed)
    
# Fix 3: Use os.getenv to pull your actual Discord token securely from the .env file
bot.run(os.getenv("TOKEN"))