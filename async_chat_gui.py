import asyncio
import logging
import os

from chat_reader import read_message
from connection import create_connection
from dotenv import load_dotenv
from gui import draw


logging.getLogger('asyncio').setLevel(logging.WARNING)
logging.getLogger('connection').setLevel(logging.WARNING)
logging.getLogger('chat_reader').setLevel(logging.DEBUG)
logging.basicConfig(level=logging.DEBUG, format='%(message)s')


async def read_msgs(host, port, msgs_queue):
    async with create_connection(host, port) as (reader, _):
        while True:
            message = await read_message(reader)
            msgs_queue.put_nowait(message)


async def main():
    load_dotenv()
    chat_server = os.getenv('CHAT_SERVER')
    port_read = os.getenv('CHAT_PORT_READ')

    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()

    await asyncio.gather(
        draw(messages_queue, sending_queue, status_updates_queue),
        read_msgs(chat_server, port_read, messages_queue)
    )


if __name__ == '__main__':
    asyncio.run(main())
