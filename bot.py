"""Discord bot for War Bot timer tracking system."""

import discord
from discord.ext import commands, tasks
import os
from dotenv import load_dotenv
import requests
from datetime import datetime, timedelta, timezone
import logging
import time
import json

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
DASHBOARD_CHANNEL_ID = int(os.getenv('DASHBOARD_CHANNEL_ID', '0')) if os.getenv('DASHBOARD_CHANNEL_ID') else None
ALERT_CHANNEL_ID = int(os.getenv('ALERT_CHANNEL_ID', '0')) if os.getenv('ALERT_CHANNEL_ID') else None

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Global variables for dashboard tracking
dashboard_message_id = None
dashboard_channel_id = None
alerted_timers = set()  # Track which timers we've already alerted for


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


def get_timers_from_api():
    """
    Fetch all timers from the API.

    Returns:
        list: List of timer dictionaries, or empty list on error
    """
    try:
        headers = {"X-API-Key": API_KEY} if API_KEY else {}
        response = requests.get(f"{API_URL}/timers/?limit=500", headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to fetch timers: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"Error fetching timers: {e}")
        return []


def format_timer_dashboard(timers):
    """
    Format timers into a Discord embed for the dashboard.

    Args:
        timers: List of timer dictionaries from API

    Returns:
        discord.Embed: Formatted embed with all timers
    """
    embed = discord.Embed(
        title="⚔️ War Timer Dashboard",
        description=f"Active Timers: {len(timers)}",
        color=discord.Color.blue(),
        timestamp=datetime.now(timezone.utc)
    )

    if not timers:
        embed.add_field(name="No Active Timers", value="Use `!im_hit`, `!pro_whack`, or `!enemy_hit` to add timers.", inline=False)
        return embed

    # Group timers by type
    friendly_hits = [t for t in timers if t['timer_type'] == 'friendly_hit']
    pro_whacks = [t for t in timers if t['timer_type'] == 'pro_whack']
    enemy_hits = [t for t in timers if t['timer_type'] == 'enemy_hit']

    # Format friendly hits
    if friendly_hits:
        friendly_text = ""
        for timer in friendly_hits[:10]:  # Limit to 10 per type
            time_shot = datetime.fromisoformat(timer['time_shot'].replace('Z', '+00:00'))
            pro_start = datetime.fromisoformat(timer['pro_drop_start'].replace('Z', '+00:00')) if timer.get('pro_drop_start') else None
            pro_end = datetime.fromisoformat(timer['pro_drop_end'].replace('Z', '+00:00')) if timer.get('pro_drop_end') else None

            friendly_text += f"**{timer['user_name']}** - Hit: `{time_shot.strftime('%H:%M:%S')}`\n"
            if pro_start and pro_end:
                friendly_text += f"  └ Pro Drop: `{pro_start.strftime('%H:%M:%S')}` - `{pro_end.strftime('%H:%M:%S')}`\n"

        embed.add_field(name="🛡️ Friendly Hits", value=friendly_text or "None", inline=False)

    # Format pro whacks
    if pro_whacks:
        pro_text = ""
        for timer in pro_whacks[:10]:
            time_shot = datetime.fromisoformat(timer['time_shot'].replace('Z', '+00:00'))
            pro_drop = datetime.fromisoformat(timer['pro_drop_start'].replace('Z', '+00:00')) if timer.get('pro_drop_start') else None

            pro_text += f"**{timer['user_name']}** - Whacked: `{time_shot.strftime('%H:%M:%S')}`\n"
            if pro_drop:
                pro_text += f"  └ Pro Drop: `{pro_drop.strftime('%H:%M:%S')}`\n"

        embed.add_field(name="💀 Pro Whacks", value=pro_text or "None", inline=False)

    # Format enemy hits
    if enemy_hits:
        enemy_text = ""
        for timer in enemy_hits[:10]:
            time_shot = datetime.fromisoformat(timer['time_shot'].replace('Z', '+00:00'))
            pro_start = datetime.fromisoformat(timer['pro_drop_start'].replace('Z', '+00:00')) if timer.get('pro_drop_start') else None

            enemy_text += f"**{timer['user_name']}** - Hit: `{time_shot.strftime('%H:%M:%S')}`\n"
            if pro_start:
                enemy_text += f"  └ Pro Drop Start: `{pro_start.strftime('%H:%M:%S')}`\n"

        embed.add_field(name="⚔️ Enemy Hits", value=enemy_text or "None", inline=False)

    embed.set_footer(text="Updates every 5 seconds")
    return embed


@tasks.loop(seconds=5)
async def update_dashboard():
    """Background task to update the dashboard every 5 seconds."""
    global dashboard_message_id, dashboard_channel_id

    if not dashboard_channel_id or not dashboard_message_id:
        return

    try:
        channel = bot.get_channel(dashboard_channel_id)
        if not channel:
            logger.warning(f"Dashboard channel {dashboard_channel_id} not found")
            return

        message = await channel.fetch_message(dashboard_message_id)
        if not message:
            logger.warning(f"Dashboard message {dashboard_message_id} not found")
            return

        # Fetch timers and update embed
        timers = get_timers_from_api()
        embed = format_timer_dashboard(timers)
        await message.edit(embed=embed)

    except discord.NotFound:
        logger.error("Dashboard message was deleted")
        dashboard_message_id = None
        dashboard_channel_id = None
    except Exception as e:
        logger.error(f"Error updating dashboard: {e}")


@tasks.loop(seconds=30)
async def check_pro_drop_alerts():
    """Background task to check for upcoming Pro Drops and send alerts."""
    global alerted_timers

    try:
        timers = get_timers_from_api()
        now = datetime.now(timezone.utc)

        for timer in timers:
            timer_id = timer['id']

            # Skip if already alerted
            if timer_id in alerted_timers:
                continue

            pro_drop_start = timer.get('pro_drop_start')
            if not pro_drop_start:
                continue

            pro_drop_time = datetime.fromisoformat(pro_drop_start.replace('Z', '+00:00'))
            time_until = pro_drop_time - now

            # Alert if Pro Drop is 5-10 minutes away
            if timedelta(minutes=5) <= time_until <= timedelta(minutes=10):
                alert_channel_id = ALERT_CHANNEL_ID or dashboard_channel_id
                if not alert_channel_id:
                    continue

                channel = bot.get_channel(alert_channel_id)
                if not channel:
                    continue

                # Format alert message
                timer_type = timer['timer_type']
                user_name = timer['user_name']
                minutes = int(time_until.total_seconds() / 60)

                if timer_type == 'friendly_hit':
                    alert_msg = f"🔔 **{user_name}**, your **Pro Drop (safe) window** begins in **{minutes} minutes**! (`{pro_drop_time.strftime('%H:%M:%S')}`)"
                elif timer_type == 'pro_whack':
                    alert_msg = f"🔔 **{user_name}**, your **Pro Drop** is in **{minutes} minutes**! (`{pro_drop_time.strftime('%H:%M:%S')}`)"
                elif timer_type == 'enemy_hit':
                    alert_msg = f"🔔 **{user_name}**, **enemy Pro Drop window** begins in **{minutes} minutes**! (`{pro_drop_time.strftime('%H:%M:%S')}`)"
                else:
                    continue

                await channel.send(alert_msg)
                alerted_timers.add(timer_id)
                logger.info(f"Sent alert for timer {timer_id}")

        # Clean up old alerted timers that no longer exist
        current_timer_ids = {t['id'] for t in timers}
        alerted_timers = alerted_timers & current_timer_ids

    except Exception as e:
        logger.error(f"Error in alert check: {e}")


@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user.name}')
    print(f'Logged in as {bot.user.name}')

    # Start background tasks
    if not update_dashboard.is_running():
        update_dashboard.start()
        logger.info("Dashboard update task started")

    if not check_pro_drop_alerts.is_running():
        check_pro_drop_alerts.start()
        logger.info("Alert check task started")

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

@bot.command(name='pro_whack')
async def pro_whack(ctx, time_str: str):
    """
    Records a pro whack timer.
    Usage: !pro_whack HH:MM:SS
    """
    try:
        logger.info(f"User {ctx.author.name} invoked !pro_whack with time {time_str}")

        # Validate and parse the time string
        whack_time = datetime.strptime(time_str, '%H:%M:%S').time()

        # Combine with today's date to create a full datetime object (timezone-aware)
        now = datetime.now(timezone.utc)
        time_shot = now.replace(hour=whack_time.hour, minute=whack_time.minute, second=whack_time.second, microsecond=0)

        # If the time is in the future, assume it was for the previous day
        if time_shot > now:
            time_shot = time_shot - timedelta(days=1)
            logger.info(f"Adjusted time to previous day: {time_shot}")

        payload = {
            "user_name": ctx.author.name,
            "timer_type": "pro_whack",
            "time_shot": time_shot.isoformat()
        }

        headers = {"X-API-Key": API_KEY} if API_KEY else {}
        response = make_api_request_with_retry(f"{API_URL}/timers/", payload, headers)

        if response.status_code == 200:
            logger.info(f"Pro whack timer successfully recorded for {ctx.author.name}")
            await ctx.send(f"💀 Pro whack timer recorded for {ctx.author.name} at {time_str}.")
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
        logger.error(f"Unexpected error in pro_whack: {e}", exc_info=True)
        await ctx.send(f"An unexpected error occurred. Please contact an administrator.")


@bot.command(name='enemy_hit')
async def enemy_hit(ctx, time_str: str):
    """
    Records an enemy hit timer.
    Usage: !enemy_hit HH:MM:SS
    """
    try:
        logger.info(f"User {ctx.author.name} invoked !enemy_hit with time {time_str}")

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
            "timer_type": "enemy_hit",
            "time_shot": time_shot.isoformat()
        }

        headers = {"X-API-Key": API_KEY} if API_KEY else {}
        response = make_api_request_with_retry(f"{API_URL}/timers/", payload, headers)

        if response.status_code == 200:
            logger.info(f"Enemy hit timer successfully recorded for {ctx.author.name}")
            await ctx.send(f"⚔️ Enemy hit timer recorded for {ctx.author.name} at {time_str}.")
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
        logger.error(f"Unexpected error in enemy_hit: {e}", exc_info=True)
        await ctx.send(f"An unexpected error occurred. Please contact an administrator.")


@bot.command(name='setup_dashboard')
async def setup_dashboard(ctx):
    """
    Sets up the live-updating timer dashboard in the current channel.
    Usage: !setup_dashboard
    """
    global dashboard_message_id, dashboard_channel_id

    try:
        logger.info(f"User {ctx.author.name} invoked !setup_dashboard in channel {ctx.channel.id}")

        # Create initial empty dashboard
        timers = get_timers_from_api()
        embed = format_timer_dashboard(timers)

        message = await ctx.send(embed=embed)

        # Store the dashboard location
        dashboard_message_id = message.id
        dashboard_channel_id = ctx.channel.id

        logger.info(f"Dashboard created: message_id={dashboard_message_id}, channel_id={dashboard_channel_id}")
        await ctx.send(f"✅ Dashboard set up! It will update every 5 seconds. (Message ID: {dashboard_message_id})")

    except Exception as e:
        logger.error(f"Error setting up dashboard: {e}", exc_info=True)
        await ctx.send("Failed to set up dashboard. Please try again.")


@bot.command(name='clear_timers')
async def clear_timers(ctx):
    """
    Clears all timers (requires confirmation).
    Usage: !clear_timers
    """
    try:
        # Get all timers
        timers = get_timers_from_api()

        if not timers:
            await ctx.send("No timers to clear.")
            return

        # Delete all timers
        headers = {"X-API-Key": API_KEY} if API_KEY else {}
        deleted_count = 0

        for timer in timers:
            try:
                response = requests.delete(
                    f"{API_URL}/timers/{timer['id']}",
                    headers=headers,
                    timeout=10
                )
                if response.status_code == 200:
                    deleted_count += 1
            except Exception as e:
                logger.error(f"Error deleting timer {timer['id']}: {e}")

        await ctx.send(f"✅ Cleared {deleted_count} timer(s).")
        logger.info(f"User {ctx.author.name} cleared {deleted_count} timers")

    except Exception as e:
        logger.error(f"Error clearing timers: {e}", exc_info=True)
        await ctx.send("Failed to clear timers. Please try again.")


@bot.command(name='whacked')
async def whacked(ctx, player_name: str = None):
    """
    Quick command to record a pro whack using current time.
    Usage: !whacked PlayerName  OR  !whacked (uses your name)
    Example: !whacked Mucci
    """
    try:
        # Use provided name or command invoker's name
        if player_name is None:
            player_name = ctx.author.name

        # Get current time
        now = datetime.now(timezone.utc)

        logger.info(f"User {ctx.author.name} invoked !whacked for {player_name}")

        payload = {
            "user_name": player_name,
            "timer_type": "pro_whack",
            "time_shot": now.isoformat()
        }

        headers = {"X-API-Key": API_KEY} if API_KEY else {}
        response = make_api_request_with_retry(f"{API_URL}/timers/", payload, headers)

        if response.status_code == 200:
            # Calculate Pro Drop time
            pro_drop = now + timedelta(minutes=15)

            logger.info(f"Pro whack timer recorded for {player_name}")
            await ctx.send(
                f"💀 **{player_name}** was whacked at `{now.strftime('%H:%M:%S')}`\n"
                f"└─ **Pro Drop:** `{pro_drop.strftime('%H:%M:%S')}`"
            )
        else:
            logger.error(f"API error: status {response.status_code}")
            await ctx.send(f"Error recording timer. Please try again.")

    except requests.RequestException as e:
        logger.error(f"Network error: {e}")
        await ctx.send("Failed to connect to the API. Please try again later.")
    except Exception as e:
        logger.error(f"Unexpected error in whacked: {e}", exc_info=True)
        await ctx.send(f"An unexpected error occurred. Please contact an administrator.")


@bot.command(name='hit')
async def hit(ctx, player_name: str = None):
    """
    Quick command to record a friendly hit using current time.
    Usage: !hit PlayerName  OR  !hit (uses your name)
    Example: !hit Mucci
    """
    try:
        # Use provided name or command invoker's name
        if player_name is None:
            player_name = ctx.author.name

        # Get current time
        now = datetime.now(timezone.utc)

        logger.info(f"User {ctx.author.name} invoked !hit for {player_name}")

        payload = {
            "user_name": player_name,
            "timer_type": "friendly_hit",
            "time_shot": now.isoformat()
        }

        headers = {"X-API-Key": API_KEY} if API_KEY else {}
        response = make_api_request_with_retry(f"{API_URL}/timers/", payload, headers)

        if response.status_code == 200:
            # Calculate Pro Drop window
            pro_start = now + timedelta(hours=3, minutes=40)
            pro_end = now + timedelta(hours=4, minutes=20)

            logger.info(f"Friendly hit timer recorded for {player_name}")
            await ctx.send(
                f"🛡️ **{player_name}** was hit at `{now.strftime('%H:%M:%S')}`\n"
                f"└─ **Pro Drop (safe window):** `{pro_start.strftime('%H:%M:%S')}` - `{pro_end.strftime('%H:%M:%S')}`"
            )
        else:
            logger.error(f"API error: status {response.status_code}")
            await ctx.send(f"Error recording timer. Please try again.")

    except requests.RequestException as e:
        logger.error(f"Network error: {e}")
        await ctx.send("Failed to connect to the API. Please try again later.")
    except Exception as e:
        logger.error(f"Unexpected error in hit: {e}", exc_info=True)
        await ctx.send(f"An unexpected error occurred. Please contact an administrator.")


@bot.command(name='enemy')
async def enemy(ctx, player_name: str = None):
    """
    Quick command to record an enemy hit using current time.
    Usage: !enemy PlayerName  OR  !enemy (uses your name)
    Example: !enemy Mucci
    """
    try:
        # Use provided name or command invoker's name
        if player_name is None:
            player_name = ctx.author.name

        # Get current time
        now = datetime.now(timezone.utc)

        logger.info(f"User {ctx.author.name} invoked !enemy for {player_name}")

        payload = {
            "user_name": player_name,
            "timer_type": "enemy_hit",
            "time_shot": now.isoformat()
        }

        headers = {"X-API-Key": API_KEY} if API_KEY else {}
        response = make_api_request_with_retry(f"{API_URL}/timers/", payload, headers)

        if response.status_code == 200:
            # Calculate Pro Drop start
            pro_start = now + timedelta(hours=3, minutes=40)

            logger.info(f"Enemy hit timer recorded for {player_name}")
            await ctx.send(
                f"⚔️ **{player_name}** got hit by enemy at `{now.strftime('%H:%M:%S')}`\n"
                f"└─ **Enemy Pro Drop starts:** `{pro_start.strftime('%H:%M:%S')}`"
            )
        else:
            logger.error(f"API error: status {response.status_code}")
            await ctx.send(f"Error recording timer. Please try again.")

    except requests.RequestException as e:
        logger.error(f"Network error: {e}")
        await ctx.send("Failed to connect to the API. Please try again later.")
    except Exception as e:
        logger.error(f"Unexpected error in enemy: {e}", exc_info=True)
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
