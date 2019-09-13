import asyncio
import logging
import time

from async_timeout import timeout


watchdog_logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(message)s')


async def watch_for_connection(watchdog_queue, conn_timeout=5):
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
