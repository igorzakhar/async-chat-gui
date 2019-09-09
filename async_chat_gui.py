import asyncio
import logging
import os

from aiofile import AIOFile
from chat_reader import read_message
from connection import create_connection
from dotenv import load_dotenv
from gui import draw


logging.getLogger('asyncio').setLevel(logging.WARNING)
logging.getLogger('connection').setLevel(logging.WARNING)
logging.getLogger('chat_reader').setLevel(logging.DEBUG)

logger = logging.getLogger('async_chat_gui')
logging.basicConfig(level=logging.DEBUG, format='%(name)s - %(message)s')


async def read_msgs(host, port, msgs_queue, save_queue):
    async with create_connection(host, port) as (reader, _):
        while True:
            message = await read_message(reader)
            msgs_queue.put_nowait(message)
            save_queue.put_nowait(message)


async def save_messages(filepath, save_queue):
    try:
        async with AIOFile(filepath, 'a') as afp:
            while True:
                message = await save_queue.get()
                await afp.write(message)
    except FileNotFoundError as err:
        logger.exception(f'{err.strerror}: {err.filename}', exc_info=False)
        sys.exit(err.errno)


async def main():
    load_dotenv()
    chat_server = os.getenv('CHAT_SERVER')
    port_read = os.getenv('CHAT_PORT_READ')
    history_file = os.getenv('CHAT_HISTORY_FILE', 'chat.history')

    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()
    save_msgs_queue = asyncio.Queue()

    await asyncio.gather(
        draw(messages_queue, sending_queue, status_updates_queue),
        read_msgs(chat_server, port_read, messages_queue, save_msgs_queue),
        save_messages(history_file, save_msgs_queue)
    )


if __name__ == '__main__':
    asyncio.run(main())
