import asyncio
import json

from .chat_reader import read_message
from .chat_writer import write_message


async def register_new_user(reader, writer, username=None):
    await read_message(reader)
    await write_message(writer)
    await read_message(reader)

    if username:
        await write_message(writer, f'{username}\n')
    else:
        await write_message(writer)
    account_info = await read_message(reader)
    return json.loads(account_info)
