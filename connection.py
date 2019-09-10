import asyncio
import contextlib
import logging


logger = logging.getLogger(__name__)


async def _get_network_streams(host, port, log_file, attempts, timeout):
    attempts_count = 0
    reader = None
    writer = None
    while not reader:
        try:
            reader, writer = await asyncio.open_connection(host, port)
            success_message = 'Установлено соединение.'
            logger.debug(success_message)

            if log_file:
                await write_message_to_file(success_message, log_file)

        except (ConnectionRefusedError, ConnectionResetError):

            if attempts_count < attempts:
                error_message = 'Нет соединения. Повторная попытка.'
                logger.debug(error_message)

                if log_file:
                    await write_message_to_file(error_message, log_file)

                attempts_count += 1

                continue

            else:
                error_message = (
                    f'Нет соединения. '
                    f'Повторная попытка через {timeout} сек.'
                )
                logger.debug(error_message)

                if log_file:
                    await write_message_to_file(error_message, log_file)

                await asyncio.sleep(timeout)

    return reader, writer


@contextlib.asynccontextmanager
async def create_connection(host, port, attempts=1, timeout=3, log_file=None):
    reader, writer = await _get_network_streams(
        host,
        port,
        log_file,
        attempts,
        timeout
    )
    try:
        yield reader, writer
    finally:
        writer.close()
