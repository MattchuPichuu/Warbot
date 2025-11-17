
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import requests
from datetime import datetime

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

@bot.command(name='im_hit')
async def im_hit(ctx, time_str: str):
    """
    Records a timer.
    Usage: !im_hit HH:MM:SS
    """
    try:
        # Validate and parse the time string
        hit_time = datetime.strptime(time_str, '%H:%M:%S').time()
        
        # Combine with today's date to create a full datetime object
        now = datetime.now()
        time_shot = now.replace(hour=hit_time.hour, minute=hit_time.minute, second=hit_time.second, microsecond=0)

        # If the time is in the future, assume it was for the previous day
        if time_shot > now:
            time_shot = time_shot - timedelta(days=1)

        payload = {
            "user_name": ctx.author.name,
            "timer_type": "friendly_hit",
            "time_shot": time_shot.isoformat()
        }

        response = requests.post("http://127.0.0.1:8000/timers", json=payload)

        if response.status_code == 200:
            await ctx.send(f"Timer recorded for {ctx.author.name} at {time_str}.")
        else:
            await ctx.send(f"Error recording timer. API returned status code: {response.status_code}")
            print(response.text)

    except ValueError:
        await ctx.send("Invalid time format. Please use HH:MM:SS.")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")
        print(e)

if __name__ == "__main__":
    if TOKEN is None:
        print("Error: DISCORD_TOKEN not found. Make sure to set it in your .env file.")
    else:
        bot.run(TOKEN)
