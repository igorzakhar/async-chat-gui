import asyncio
import logging


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(message)s')


async def write_message(writer, message=None):
    if not message:
        message = '\n'
    writer.write(message.encode())
    logger.debug(f'Sent message: {message!r}')
    await writer.drain()
