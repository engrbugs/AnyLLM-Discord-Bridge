import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import requests
import json
import logging
import psutil

API_TIMEOUT = 90
SILENT_MODE = True

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
ANYTHINGLLM_API_KEY = os.getenv("ANYTHINGLLM_API_KEY")
ANYTHINGLLM_API_URL = os.getenv("ANYTHINGLLM_API_URL")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))  # Load from .env and convert to int

# Validate environment variables
if not all([DISCORD_TOKEN, ANYTHINGLLM_API_KEY, ANYTHINGLLM_API_URL, CHANNEL_ID]):
    logger.error("Missing environment variables. Check .env file.")
    exit(1)

# Define intents
intents = discord.Intents.default()
intents.message_content = True  # Enable reading message content

# Initialize bot with command prefix
bot = commands.Bot(command_prefix="!", intents=intents)

def get_current_thread_slug():
    """Fetch the latest thread slug from the discord workspace."""
    headers = {
        "Authorization": f"Bearer {ANYTHINGLLM_API_KEY}",
        "Accept": "application/json"
    }
    try:
        response = requests.get(
            f"{ANYTHINGLLM_API_URL}/workspaces",
            headers=headers,
            timeout=API_TIMEOUT
        )
        response.raise_for_status()
        data = response.json()
        threads = next((ws["threads"] for ws in data["workspaces"] if ws["slug"] == "discord"), [])
        return threads[0]["slug"] if threads else None
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch thread slug: {str(e)}")
        return None

def clear_and_create_thread():
    """Clear all threads in discord workspace and create a new one."""
    headers = {
        "Authorization": f"Bearer {ANYTHINGLLM_API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    try:
        # Fetch current threads
        response = requests.get(
            f"{ANYTHINGLLM_API_URL}/workspaces",
            headers=headers,
            timeout=API_TIMEOUT
        )
        response.raise_for_status()
        data = response.json()
        threads = next((ws["threads"] for ws in data["workspaces"] if ws["slug"] == "discord"), [])

        # Delete all threads
        for thread in threads:
            response = requests.delete(
                f"{ANYTHINGLLM_API_URL}/workspace/discord/thread/{thread['slug']}",
                headers=headers,
                timeout=API_TIMEOUT
            )
            response.raise_for_status()
            logger.info(f"Deleted thread {thread['slug']} in discord workspace")

        # Create new thread
        response = requests.post(
            f"{ANYTHINGLLM_API_URL}/workspace/discord/thread/new",
            headers=headers,
            json={"name": "Discord Thread"},
            timeout=API_TIMEOUT
        )
        response.raise_for_status()
        new_thread = response.json().get("thread", {})
        logger.info(f"Created new thread {new_thread.get('slug', 'unknown')} in discord workspace")
        return new_thread.get("slug", None)
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to clear/create thread: {str(e)}")
        return None

@bot.event
async def on_ready():
    logger.info(f"{bot.user} is connected to Discord!")
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        # Clear threads and create new one on startup
        new_thread_slug = clear_and_create_thread()
        if not SILENT_MODE:
            if new_thread_slug:
                await channel.send(f"Pepper bot is online with new thread: {new_thread_slug}")
            else:
                await channel.send("Pepper bot is online, but I think AnythingLLM is offline.")
        logger.info(f"Startup message sent to channel {CHANNEL_ID} (silent: {SILENT_MODE})")
    else:
        logger.error(f"Channel {CHANNEL_ID} not found. Check CHANNEL_ID in .env.")

@bot.event
async def on_message(message):
    if message.author == bot.user or message.channel.id != CHANNEL_ID:
        return

    # Skip commands with ! prefix
    if message.content.startswith("!"):
        await bot.process_commands(message)
        return

    logger.info(f"Received message from {message.author}: {message.content}")
    headers = {
        "Authorization": f"Bearer {ANYTHINGLLM_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    thread_slug = get_current_thread_slug()
    if not thread_slug:
        await message.channel.send("Error: No thread available. Try !clear to create a new thread.")
        logger.error("No thread slug found for chatting")
        return

    payload = {
        "message": message.content,
        "mode": "chat",
        "userId": 1,
        "attachments": [],
        "reset": False
    }
    try:
        response = requests.post(
            f"{ANYTHINGLLM_API_URL}/workspace/discord/thread/{thread_slug}/chat",
            headers=headers,
            json=payload,
            timeout=API_TIMEOUT
        )
        response.raise_for_status()
        data = response.json()
        reply = data.get("textResponse", "No response from AnythingLLM.")
        await message.channel.send(reply)
        logger.info(f"Sent response to {message.author}: {reply[:50]}...")
    except requests.exceptions.Timeout:
        logger.error(f"API timed out after {API_TIMEOUT} seconds")
        await message.channel.send("Error: API timed out.")
    except requests.exceptions.HTTPError as e:
        logger.error(f"API HTTP error: {e.response.status_code} - {e.response.text}")
        await message.channel.send(f"Error: API returned {e.response.status_code}.")
    except requests.exceptions.RequestException as e:
        logger.error(f"API connection error: {str(e)}")
        await message.channel.send(f"Error connecting to AnythingLLM: {str(e)}")

    await bot.process_commands(message)

@bot.command()
async def ping(ctx):
    """Check bot and AnythingLLM API status."""
    if ctx.channel.id != CHANNEL_ID:
        return

    # Check bot status
    bot_status = "Pong! Bot is online."
    logger.info(f"Ping command executed by {ctx.author}: Bot is online")

    # Check AnythingLLM API status
    headers = {
        "Authorization": f"Bearer {ANYTHINGLLM_API_KEY}",
        "Accept": "application/json"
    }
    try:
        response = requests.get(
            f"{ANYTHINGLLM_API_URL}/auth",
            headers=headers,
            timeout=60
        )
        response.raise_for_status()
        data = response.json()
        api_status = "AnythingLLM API is online." if data.get("authenticated") else "API authentication failed."
        logger.info(f"LLM status checked by {ctx.author}: {api_status}")
    except requests.exceptions.Timeout:
        logger.error("API timed out after 60 seconds")
        api_status = "Error: API timed out."
    except requests.exceptions.HTTPError as e:
        logger.error(f"API HTTP error: {e.response.status_code} - {e.response.text}")
        api_status = f"Error: API returned {e.response.status_code}."
    except requests.exceptions.RequestException as e:
        logger.error(f"API connection error: {str(e)}")
        api_status = f"Error connecting to AnythingLLM: {str(e)}"

    # Combine responses
    await ctx.send(f"{bot_status}\n{api_status}")


@bot.command()
async def pepper(ctx):
    """Check if pepper.exe is running on the system."""
    if ctx.channel.id != CHANNEL_ID:
        return

    is_running = any(proc.name().lower() == "pepper.exe" for proc in psutil.process_iter(['name']))
    if is_running:
        await ctx.send("pepper.exe is running.")
    else:
        await ctx.send("pepper.exe is NOT running.")
@bot.command()
async def clear(ctx):
    """Clear all chats in the discord workspace by deleting all threads and creating a new one."""
    if ctx.channel.id != CHANNEL_ID:
        return

    new_thread_slug = clear_and_create_thread()
    if new_thread_slug:
        await ctx.send(f"Workspace chats cleared and new thread created: {new_thread_slug}")
        logger.info(f"Cleared all threads and created new thread by {ctx.author}")
    else:
        await ctx.send("Failed to clear chats or create new thread.")
        logger.error(f"Failed to clear threads or create new thread by {ctx.author}")

@bot.command()
async def reconnect(ctx):
    """Reconnect to AnythingLLM by resetting threads and creating a new one."""
    if ctx.channel.id != CHANNEL_ID:
        return

    logger.info(f"Reconnect command executed by {ctx.author}")
    new_thread_slug = clear_and_create_thread()
    if new_thread_slug:
        await ctx.send(f"Reconnected to AnythingLLM with new thread: {new_thread_slug}")
        logger.info(f"Successfully reconnected and created new thread: {new_thread_slug}")
    else:
        await ctx.send("Failed to reconnect to AnythingLLM. Check if the API is online.")
        logger.error(f"Failed to reconnect by {ctx.author}")


bot.run(DISCORD_TOKEN)