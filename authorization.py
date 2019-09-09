import asyncio
import json
import logging
from tkinter import messagebox

from chat_reader import read_message
from chat_writer import write_message


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(message)s')


class InvalidToken(Exception):
    pass


async def is_authorized(reader, writer, token):
    data = await read_message(reader)
    await write_message(writer, f'{token}\n')
    data = await read_message(reader)
    account_data = json.loads(data)
    if account_data is None:
        return False, None
    return True, account_data.get('nickname')


async def user_authorization(reader, writer, token):
    authorized, nickname = await is_authorized(reader, writer, token)
    if not authorized:
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
        logger.debug(
            'Выполнена авторизация.'
            f'Пользователь {nickname}.'
        )
    return authorized, nickname
