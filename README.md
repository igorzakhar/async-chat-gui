# Асинхронная версия клиента для чата с GUI.

Версия клиента с графическим интерфейсом для подключения к серверу чата. Отдельным модулем (user_registration.py) реализована регистрация нового пользователя через графический интерфейс.

## Как установить

Для запуска скриптов нужен предустановленный Python версии не ниже 3.7+.
Также в программе используются следующие сторонние библиотеки:
- aiofile [https://github.com/mosquito/aiofile](https://github.com/mosquito/aiofile);
- aionursery [https://github.com/malinoff/aionursery](https://github.com/malinoff/aionursery).
- async-timeout [https://github.com/aio-libs/async-timeout](https://github.com/aio-libs/async-timeout).
- python-dotenv [https://github.com/theskumar/python-dotenv](https://github.com/theskumar/python-dotenv).

Рекомендуется устанавливать зависимости в виртуальном окружении, используя [virtualenv](https://github.com/pypa/virtualenv), [virtualenvwrapper](https://pypi.python.org/pypi/virtualenvwrapper) или [venv](https://docs.python.org/3/library/venv.html).

1. Скопируйте репозиторий в текущий каталог. Воспользуйтесь командой:
```bash
$ git clone https://github.com/igorzakhar/async-chat-gui.git async_chat_gui
```
После этого программа будет скопирована в каталог ```async_chat_gui```

2. Создайте и активируйте виртуальное окружение:
```bash
$ cd async_chat_gui# Переходим в каталог с программой
$ python3 -m venv my_virtual_environment # Создаем виртуальное окружение
$ source my_virtual_environment/bin/activate # Активируем виртуальное окружение
```

3. Установите сторонние библиотеки  из файла зависимостей:
```bash
$ pip install -r requirements.txt # В качестве альтернативы используйте pip3
```

# Настройка приложения

Создайте ```.env``` файл c необходимыми параметрами, такими как:
```
CHAT_SERVER=minechat.dvmn.org
CHAT_PORT_READ=5000
CHAT_PORT_SEND=5050
```
Если вы являетесь зарегстрированным пользователем чата, необходимо добавить параметр ```CHAT_TOKEN='ваш токен'```, иначе воспользуйтесь скриптом для регистрации нового пользователя ```user_registration.py```.

Необязательные параметры:
```
CHAT_HISTORY_FILE - путь до файла где хранится история переписки. По умолчанию: текущая_директория/chat.history
```

# Запуск приложения

##### 1. Запуск клиента для зарегистрированного пользователя.
Предполагается наличие токена для доступа к чату. Токен для чата хранится в переменной окружения ```CHAT_TOKEN```(можно прописать в файле ```.env```). При отсутствии переменной окружения ```CHAT_TOKEN``` скрипт пытается прочитать токен из файла ```access_token.txt```. В случае если данный файл не найден скрипт выдаст предупреждение.  
Пример запуска скрипта:
```bash
$ python3 async_chat_gui.py
```

##### 2. Запуск скрипта для регистрации нового пользователя.
```bash
$ python3 user_registration.py
```
После запуска будет предложено выбрать имя пользователя которое будет отображаться в чате. После регистрации токен для  доступа в чате сохранится в файл ```access_token.txt```.

# Цели проекта

Код написан в учебных целях — это урок в курсе по Python и веб-разработке на сайте [Devman](https://dvmn.org).
