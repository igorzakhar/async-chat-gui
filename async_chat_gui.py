import asyncio
import logging
import os
import sys
import time

from aiofile import AIOFile, LineReader
from async_timeout import timeout
from authorization import user_authorization, InvalidToken
from chat_reader import read_message
from chat_writer import write_message
from connection import create_connection
from dotenv import load_dotenv
from gui import (
    draw,
    TkAppClosed,
    NicknameReceived,
    ReadConnectionStateChanged,
    SendingConnectionStateChanged
)

logging.getLogger('asyncio').setLevel(logging.WARNING)
logging.getLogger('connection').setLevel(logging.WARNING)
logging.getLogger('chat_reader').setLevel(logging.WARNING)
logging.getLogger('chat_writer').setLevel(logging.WARNING)
logging.getLogger('authorization').setLevel(logging.WARNING)

logger = logging.getLogger('async_chat_gui')
logger.setLevel(logging.INFO)

watchdog_logger = logging.getLogger('watchdog_logger')
watchdog_logger.setLevel(logging.INFO)


async def read_msgs(
        host, port, msgs_queue, save_queue, status_queue, watchdog_queue):
    status_queue.put_nowait(ReadConnectionStateChanged.INITIATED)

    try:
        async with create_connection(host, port) as (reader, _):
            status_queue.put_nowait(ReadConnectionStateChanged.ESTABLISHED)

            while True:
                message = await read_message(reader)
                msgs_queue.put_nowait(message)
                save_queue.put_nowait(message)
                watchdog_queue.put_nowait('New message in chat')

    finally:
        status_queue.put_nowait(ReadConnectionStateChanged.CLOSED)


async def send_msgs(
        host, port, send_queue, status_queue, watchdog_queue, token):
    status_queue.put_nowait(SendingConnectionStateChanged.INITIATED)

    try:
        async with create_connection(host, port) as (reader, writer):
            status_queue.put_nowait(SendingConnectionStateChanged.ESTABLISHED)

            watchdog_queue.put_nowait('Prompt before auth')
            auth, nickname = await user_authorization(reader, writer, token)

            watchdog_queue.put_nowait('Authorization done')
            status_queue.put_nowait(NicknameReceived(nickname))

            while True:
                message = await send_queue.get()
                await write_message(writer, f'{message}\n\n')
                watchdog_queue.put_nowait('Message sent')

    finally:
        status_queue.put_nowait(SendingConnectionStateChanged.CLOSED)


async def watch_for_connection(watchdog_queue, conn_timeout=5, debug=False):
    if debug:
        watchdog_logger.setLevel(logging.DEBUG)

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


async def save_messages(filepath, save_queue):
    try:
        async with AIOFile(filepath, 'a') as afp:
            while True:
                message = await save_queue.get()
                await afp.write(f'{message}\n')
    except FileNotFoundError as err:
        logger.exception(f'{err.strerror}: {err.filename}', exc_info=False)
        sys.exit(err.errno)


async def restore_chat_history(filename, msgs_queue):
    try:
        async with AIOFile(filename, 'rb') as afp:
            async for line in LineReader(afp):
                msgs_queue.put_nowait(line.decode().strip())
    except FileNotFoundError as err:
        logger.exception(f'{err.strerror}: {err.filename}', exc_info=False)
        pass


async def main():
    load_dotenv()
    chat_server = os.getenv('CHAT_SERVER')
    port_read = os.getenv('CHAT_PORT_READ')
    port_send = os.getenv('CHAT_PORT_SEND')
    history_file = os.getenv('CHAT_HISTORY_FILE', 'chat.history')
    chat_token = os.getenv('CHAT_TOKEN')

    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()
    save_msgs_queue = asyncio.Queue()
    watchdog_queue = asyncio.Queue()

    await restore_chat_history(history_file, messages_queue)

    await asyncio.gather(
        draw(messages_queue, sending_queue, status_updates_queue),
        read_msgs(
            chat_server,
            port_read,
            messages_queue,
            save_msgs_queue,
            status_updates_queue,
            watchdog_queue,
        ),
        send_msgs(
            chat_server,
            port_send,
            sending_queue,
            status_updates_queue,
            watchdog_queue,
            chat_token
        ),
        save_messages(history_file, save_msgs_queue),
        watch_for_connection(watchdog_queue, debug=True)
    )


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, TkAppClosed, InvalidToken):
        sys.exit()
