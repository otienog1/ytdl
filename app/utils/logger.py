import sys
from loguru import logger
from app.config.settings import settings

# Remove default handler
logger.remove()

# Add custom handlers
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="DEBUG" if settings.ENVIRONMENT == "development" else "INFO"
)

logger.add(
    "logs/error.log",
    rotation="500 MB",
    retention="10 days",
    level="ERROR",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}"
)

logger.add(
    "logs/combined.log",
    rotation="500 MB",
    retention="10 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}"
)
