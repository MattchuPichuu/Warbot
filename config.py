"""Configuration management for the War Bot application."""
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class BotConfig:
    """Configuration for Discord bot."""

    DISCORD_TOKEN: Optional[str] = os.getenv('DISCORD_TOKEN')
    API_KEY: Optional[str] = os.getenv('API_KEY')
    API_URL: str = os.getenv('API_URL', 'http://127.0.0.1:8000')
    COMMAND_PREFIX: str = os.getenv('COMMAND_PREFIX', '!')

    # Retry configuration
    MAX_API_RETRIES: int = int(os.getenv('MAX_API_RETRIES', '3'))
    API_TIMEOUT: int = int(os.getenv('API_TIMEOUT', '10'))


class APIConfig:
    """Configuration for FastAPI backend."""

    API_KEY: Optional[str] = os.getenv('API_KEY')
    DATABASE_URL: str = os.getenv('DATABASE_URL', 'sqlite:///./war_timer.db')

    # API limits
    MAX_QUERY_LIMIT: int = int(os.getenv('MAX_QUERY_LIMIT', '500'))

    # Logging
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')


class Config:
    """Main configuration class."""

    bot = BotConfig()
    api = APIConfig()
