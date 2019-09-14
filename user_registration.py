import argparse
import asyncio
import json
import logging
import os
import sys
import tkinter as tk
from tkinter import messagebox

from aiofile import AIOFile
from dotenv import load_dotenv
from guichat.chat_reader import read_message
from guichat.chat_writer import write_message
from guichat.gui import update_tk
from guichat.gui import TkAppClosed
from guichat.connection import create_connection
from guichat.utils import create_handy_nursery


logging.getLogger('asyncio').setLevel(logging.WARNING)
logging.getLogger('guichat').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(message)s')


class RegistrationComplete(Exception):
    pass


async def registration_new_user(host, port, reg_queue, filepath=None):
    async with create_connection(host, port) as (reader, writer):
        username = ''
        while not username:
            username = await reg_queue.get()
            if username == '':
                messagebox.showinfo(
                    'Введите имя пользователя',
                )
        logger.debug(f'Username entered: {username}')

        user_data = await request_for_registration(reader, writer, username)
        logger.debug(f'Response data: {user_data}')

        nickname = user_data.get('nickname')
        token = user_data.get('account_hash')

        if filepath is None:
            filepath = 'access_token.txt'
        await save_token(filepath, token)
        messagebox.showinfo(
            'Регистрация завершена',
            f'Ваше имя в чате: {nickname}\n'
            f'Токен сохранен в файле: {filepath}'
        )
        raise RegistrationComplete


async def request_for_registration(reader, writer, username):
    await read_message(reader)
    await write_message(writer)
    await read_message(reader)

    if username:
        await write_message(writer, f'{username}\n')
    else:
        await write_message(writer)
    account_info = await read_message(reader)
    return json.loads(account_info)


async def save_token(filepath, token):
    async with AIOFile(filepath, 'w') as afp:
        await afp.write(token)


def get_username(username_input, reg_queue):
    username = username_input.get()
    reg_queue.put_nowait(username)
    username_input.delete(0, tk.END)


async def draw_registration_window(reg_queue):
    root = tk.Tk()
    root.title('Регистрация нового пользователя')

    root_frame = tk.Frame(root, width=380)
    root_frame.pack(pady=10)

    label = tk.Label(
        width=25,
        height=1,
        text='Введите имя пользователя'
    )
    label.pack()

    username_input = tk.Entry(width=20)
    username_input.pack(pady=5)

    register_button = tk.Button(text='Зарегистрироваться', bd=1)
    register_button.bind(
        '<Button-1>', lambda event: get_username(
            username_input,
            reg_queue
        )
    )
    register_button.pack(pady=10)

    async with create_handy_nursery() as nursery:
        nursery.start_soon(update_tk(root_frame))


def process_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--debug', action="store_true", help='Debug mode.'
    )

    return parser.parse_args()


async def main():
    load_dotenv()
    args = process_args()
    if args.debug:
        logger.setLevel(logging.DEBUG)
    chat_server = os.getenv('CHAT_SERVER')
    port_send = os.getenv('CHAT_PORT_SEND')

    registration_queue = asyncio.Queue()

    async with create_handy_nursery() as nursery:
        nursery.start_soon(
            draw_registration_window(registration_queue)
        )

        nursery.start_soon(
            registration_new_user(chat_server, port_send, registration_queue)
        )


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (TkAppClosed, KeyboardInterrupt, RegistrationComplete):
        sys.exit()
