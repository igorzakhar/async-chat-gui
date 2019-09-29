import asyncio
import logging

from .log import logger


async def write_message(writer, message=None):
    if not message:
        message = '\n'
    else:
        message = message.replace('\n', '').strip()
        message = f'{message}\n\n'
    writer.write(message.encode())
    logger.debug(f'Sent message: {message!r}')
    await writer.drain()
