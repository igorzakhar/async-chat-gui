import asyncio
import logging
import os
import sys

from aiofile import AIOFile, LineReader
from authorization import user_authorization
from chat_reader import read_message
from chat_writer import write_message
from connection import create_connection
from dotenv import load_dotenv
from gui import draw, TkAppClosed


logging.getLogger('asyncio').setLevel(logging.WARNING)
logging.getLogger('connection').setLevel(logging.WARNING)
logging.getLogger('chat_reader').setLevel(logging.WARNING)
logging.getLogger('chat_writer').setLevel(logging.WARNING)
logging.getLogger('authorization').setLevel(logging.DEBUG)

logger = logging.getLogger('async_chat_gui')
logger.setLevel(logging.DEBUG)


async def read_msgs(host, port, msgs_queue, save_queue):
    async with create_connection(host, port) as (reader, _):
        while True:
            message = await read_message(reader)
            msgs_queue.put_nowait(message)
            save_queue.put_nowait(message)


async def send_msgs(host, port, send_queue, token):
    async with create_connection(host, port) as (reader, writer):
        authorized, _ = await user_authorization(reader, writer, token)
        while True:
            message = await send_queue.get()
            await write_message(writer, f'{message}\n\n')


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

    await restore_chat_history(history_file, messages_queue)

    await asyncio.gather(
        draw(messages_queue, sending_queue, status_updates_queue),
        read_msgs(chat_server, port_read, messages_queue, save_msgs_queue),
        send_msgs(chat_server, port_send, sending_queue, chat_token),
        save_messages(history_file, save_msgs_queue)
    )


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, TkAppClosed):
        sys.exit()
