import asyncio
import contextlib
import logging
import os
import sys
import socket
from tkinter import messagebox

import aionursery
from aiofile import AIOFile
from dotenv import load_dotenv
from guichat.authorization import get_access_to_chat, InvalidToken
from guichat.chat_reader import read_message
from guichat.chat_writer import write_message
from guichat.connection import create_connection
from guichat.gui import (
    draw,
    TkAppClosed,
    NicknameReceived,
    ReadConnectionStateChanged,
    SendingConnectionStateChanged
)
from guichat.utils import create_handy_nursery
from guichat.watchdog import watch_for_connection, ping_pong


logging.getLogger('asyncio').setLevel(logging.WARNING)
logging.getLogger('guichat').setLevel(logging.INFO)
logging.getLogger('guichat.watchdog').setLevel(logging.INFO)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class TokenNotFound(Exception):
    pass


async def handle_connection(
        host, port_read, port_send, msgs_queue, send_queue,
        status_queue, save_queue, watchdog_queue, history_file, token):

    while True:
        async with contextlib.AsyncExitStack() as stack:
            status_queue.put_nowait(ReadConnectionStateChanged.INITIATED)
            status_queue.put_nowait(SendingConnectionStateChanged.INITIATED)

            reader_streams = await stack.enter_async_context(
                create_connection(host, port_read)
            )
            writer_streams = await stack.enter_async_context(
                create_connection(host, port_send)
            )

            status_queue.put_nowait(ReadConnectionStateChanged.ESTABLISHED)
            status_queue.put_nowait(SendingConnectionStateChanged.ESTABLISHED)

            try:
                if token:
                    _, nickname = await get_access_to_chat(
                        *writer_streams,
                        watchdog_queue,
                        token
                    )

                status_queue.put_nowait(NicknameReceived(nickname))

                await restore_chat_history(history_file, msgs_queue)

                async with create_handy_nursery() as nursery:
                    reader, _ = reader_streams

                    nursery.start_soon(
                        read_msgs(
                            reader,
                            msgs_queue,
                            save_queue,
                            watchdog_queue
                        )
                    )
                    nursery.start_soon(
                        send_msgs(
                            *writer_streams,
                            send_queue,
                            watchdog_queue,
                        )
                    )

                    nursery.start_soon(watch_for_connection(watchdog_queue))

                    nursery.start_soon(
                        ping_pong(*writer_streams, watchdog_queue)
                    )

            except (
                ConnectionRefusedError,
                ConnectionResetError,
                ConnectionError,
                aionursery.MultiError,
                socket.gaierror
            ):
                continue

            finally:
                status_queue.put_nowait(ReadConnectionStateChanged.CLOSED)
                status_queue.put_nowait(SendingConnectionStateChanged.CLOSED)

            break


async def read_msgs(reader, msgs_queue, save_queue, watchdog_queue):
    while True:
        message = await read_message(reader)
        msgs_queue.put_nowait(message)
        save_queue.put_nowait(message)
        watchdog_queue.put_nowait('New message in chat')


async def send_msgs(reader, writer, send_queue, watchdog_queue):
    while True:
        message = await send_queue.get()
        await write_message(writer, message)
        watchdog_queue.put_nowait('Message sent')


async def save_messages(filepath, save_queue):
    try:
        async with AIOFile(filepath, 'a') as afp:
            while True:
                message = await save_queue.get()
                await afp.write(f'{message}\n')
    except FileNotFoundError as err:
        logger.exception(f'{err.strerror}: {err.filename}', exc_info=False)
        pass


async def restore_chat_history(filename, msgs_queue):
    try:
        async with AIOFile(filename, 'r') as afp:
            messages = await afp.read()
            msgs_queue.put_nowait(messages.strip())
    except FileNotFoundError as err:
        logger.exception(f'{err.strerror}: {err.filename}', exc_info=False)
        pass


async def read_token_from_file(filepath):
    try:
        async with AIOFile(filepath, 'r') as afp:
            token = await afp.read()
            return token
    except FileNotFoundError as err:
        logger.exception(f'{err.strerror}: {err.filename}', exc_info=False)
        raise TokenNotFound('Файл не найден', 'Файл с токеном не найден.')


async def main():
    load_dotenv()
    chat_server = os.getenv('CHAT_SERVER')
    port_read = os.getenv('CHAT_PORT_READ')
    port_send = os.getenv('CHAT_PORT_SEND')
    history_file = os.getenv('CHAT_HISTORY_FILE', 'chat.history')
    token_file = os.getenv('CHAT_TOKEN_FILE', 'access_token.txt')
    chat_token = os.getenv('CHAT_TOKEN')

    if chat_token is None:
        chat_token = await read_token_from_file(token_file)

    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()
    save_msgs_queue = asyncio.Queue()
    watchdog_queue = asyncio.Queue()

    async with create_handy_nursery() as nursery:
        nursery.start_soon(
            draw(messages_queue, sending_queue, status_updates_queue)
        )

        nursery.start_soon(
            handle_connection(
                chat_server,
                port_read,
                port_send,
                messages_queue,
                sending_queue,
                status_updates_queue,
                save_msgs_queue,
                watchdog_queue,
                history_file,
                chat_token
            )
        )

        nursery.start_soon(save_messages(history_file, save_msgs_queue))


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (
        KeyboardInterrupt,
        FileNotFoundError,
        TkAppClosed,
        InvalidToken,
        TokenNotFound
    ) as err:

        if isinstance(err, TokenNotFound):
            title, message = err.args
            messagebox.showinfo(title, message)

        sys.exit()
