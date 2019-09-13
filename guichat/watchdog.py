import asyncio
import logging
import time

from async_timeout import timeout
from .chat_writer import write_message
from .chat_reader import read_message


watchdog_logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(message)s')


async def watch_for_connection(watchdog_queue, conn_timeout=10):
    while True:
        current_timestamp = int(time.time())

        try:
            async with timeout(conn_timeout):
                event = await watchdog_queue.get()
                watchdog_logger.debug(
                    f'[{current_timestamp}] Connection is alive. {event}'
                )

        except asyncio.TimeoutError:
            watchdog_logger.debug(
                f'[{current_timestamp}] {conn_timeout}s timeout is elapsed'
            )
            raise ConnectionError


async def ping_pong(
        reader, writer, watchdog_queue, conn_timeout=5, delay_send=10):

    while True:
        try:
            async with timeout(conn_timeout):
                await write_message(writer)
                await reader.readline()

            watchdog_queue.put_nowait('Ping message sent')
            await asyncio.sleep(delay_send)

        except asyncio.TimeoutError as err:
            raise ConnectionError
