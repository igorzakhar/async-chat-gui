import asyncio
import json
import logging
from tkinter import messagebox

from .chat_reader import read_message
from .chat_writer import write_message
from .log import logger


class InvalidToken(Exception):
    pass


async def authorize(reader, writer, token):
    data = await read_message(reader)
    await write_message(writer, f'{token}\n')
    data = await read_message(reader)
    account_data = json.loads(data)
    if account_data is None:
        return False, None
    return True, account_data.get('nickname')


async def get_access_to_chat(reader, writer, watchdog_queue, token):
    watchdog_queue.put_nowait('Prompt before auth')
    is_authorized, nickname = await authorize(reader, writer, token)

    if not is_authorized:
        logger.debug(
            'Неизвестный токен. '
            'Поверьте его или зарегистрируйте заново.'
        )
        messagebox.showinfo(
            'Неверный токен',
            'Поверьте токен, сервер его не узнал.'
        )
        raise InvalidToken('Your token is invalid')

    else:
        watchdog_queue.put_nowait('Authorization done')
        logger.debug(
            'Выполнена авторизация.'
            f'Пользователь {nickname}.'
        )

    return is_authorized, nickname
