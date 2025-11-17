"""Discord bot for War Bot timer tracking system."""

import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import requests
from datetime import datetime, timedelta, timezone
import logging
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
API_KEY = os.getenv('API_KEY')
API_URL = os.getenv('API_URL', 'http://127.0.0.1:8000')

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)


def make_api_request_with_retry(url: str, payload: dict, headers: dict, max_retries: int = 3) -> requests.Response:
    """
    Make an API request with exponential backoff retry logic.

    Args:
        url: API endpoint URL
        payload: JSON payload to send
        headers: Request headers
        max_retries: Maximum number of retry attempts

    Returns:
        requests.Response: API response

    Raises:
        requests.RequestException: If all retries fail
    """
    for attempt in range(max_retries):
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            return response
        except (requests.ConnectionError, requests.Timeout) as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                logger.warning(f"API request failed (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                logger.error(f"API request failed after {max_retries} attempts: {e}")
                raise
        except requests.RequestException as e:
            logger.error(f"API request error: {e}")
            raise


@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user.name}')
    print(f'Logged in as {bot.user.name}')

@bot.command(name='im_hit')
async def im_hit(ctx, time_str: str):
    """
    Records a timer.
    Usage: !im_hit HH:MM:SS
    """
    try:
        logger.info(f"User {ctx.author.name} invoked !im_hit with time {time_str}")

        # Validate and parse the time string
        hit_time = datetime.strptime(time_str, '%H:%M:%S').time()

        # Combine with today's date to create a full datetime object (timezone-aware)
        now = datetime.now(timezone.utc)
        time_shot = now.replace(hour=hit_time.hour, minute=hit_time.minute, second=hit_time.second, microsecond=0)

        # If the time is in the future, assume it was for the previous day
        if time_shot > now:
            time_shot = time_shot - timedelta(days=1)
            logger.info(f"Adjusted time to previous day: {time_shot}")

        payload = {
            "user_name": ctx.author.name,
            "timer_type": "friendly_hit",
            "time_shot": time_shot.isoformat()
        }

        headers = {"X-API-Key": API_KEY} if API_KEY else {}

        # Use retry logic for API request
        response = make_api_request_with_retry(f"{API_URL}/timers/", payload, headers)

        if response.status_code == 200:
            logger.info(f"Timer successfully recorded for {ctx.author.name}")
            await ctx.send(f"Timer recorded for {ctx.author.name} at {time_str}.")
        else:
            logger.error(f"API error: status {response.status_code}, response: {response.text}")
            await ctx.send(f"Error recording timer. API returned status code: {response.status_code}")

    except ValueError as e:
        logger.warning(f"Invalid time format from {ctx.author.name}: {time_str}")
        await ctx.send("Invalid time format. Please use HH:MM:SS.")
    except requests.RequestException as e:
        logger.error(f"Network error: {e}")
        await ctx.send("Failed to connect to the API. Please try again later.")
    except Exception as e:
        logger.error(f"Unexpected error in im_hit: {e}", exc_info=True)
        await ctx.send(f"An unexpected error occurred. Please contact an administrator.")

if __name__ == "__main__":
    if TOKEN is None:
        logger.error("DISCORD_TOKEN not found. Make sure to set it in your .env file.")
        print("Error: DISCORD_TOKEN not found. Make sure to set it in your .env file.")
    elif API_KEY is None:
        logger.warning("API_KEY not found. API requests may fail if authentication is required.")
        print("Warning: API_KEY not found. API requests may fail if authentication is required.")
        bot.run(TOKEN)
    else:
        logger.info("Starting bot...")
        bot.run(TOKEN)
