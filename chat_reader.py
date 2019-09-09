import asyncio
import logging


logger = logging.getLogger(__name__)


async def read_message(reader):
    data = await reader.readline()
    message = data.decode().rstrip()
    logger.debug(message)
    return message
