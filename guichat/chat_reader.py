import asyncio
import logging

from .log import logger


async def read_message(reader):
    data = await reader.readline()
    message = data.decode().rstrip()
    logger.debug(message)
    return message
