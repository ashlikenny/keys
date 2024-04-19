# coding: utf-8

# добавляем библиотеки для работы с ботом
import asyncio        # использование асинхронных вызовов
import logging        # логгирование информации о работе бота
import random         # генерация случайных чисел
import string         # дополнительные функции для работы со строками
import wikipedia      # для работы с wikipedia
import requests       # для отправки запросов на сторонние сервисы
import numexpr        # для вычисления выражений в строке
import json           # для работы с json строками
import re             # для использования регулярных выражений
from aiogram.filters.command import Command
from aiogram import Bot, types, Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.session.aiohttp import AiohttpSession

# указываем что будем работать с русской версией википедии
wikipedia.set_lang("ru")

# здесь указываем свой токен от бота в телеграме
TOKEN = '6323857587:AAGE5xpjQ1rRqEpPMw3-Jl3Yt6xzx7B6hg0'

# инициализируем нового бота с указанным токеном выше
session = AiohttpSession(proxy="http://proxy.server:3128")
bot = Bot(token=TOKEN, session=session)
dp = Dispatcher()

# это нужно чтобы видеть все сообщения процесса работы программы
logging.basicConfig(filename = 'log_bot.log', level = logging.INFO, force = True, format='%(asctime)s - %(levelname)s - %(message)s')

# наши кнопочки, тут у нас text - на кнопке, и callback_data - данные которые
# помогут нам определить, какая кнопка была нажата.
main_kb = InlineKeyboardMarkup(inline_keyboard = [
  # добавляем еще один ряд кнопочек
  [
    InlineKeyboardButton(text = "Статья wiki", callback_data = "wiki"),
    InlineKeyboardButton(text = "Анекдот", callback_data = "joke"),
    InlineKeyboardButton(text = "Калькулятор", callback_data = "calc")
  ],
  [
    InlineKeyboardButton(text = "Приветствие", callback_data = "greetings"),
    InlineKeyboardButton(text = "Котик", callback_data = "cat"),
    InlineKeyboardButton(text = "gif котик", callback_data = "gif_cat")
  ]
])

# это событие будет вызываться при нажатии кнопок
@dp.callback_query()
async def handle_callback_query(callback_query: types.CallbackQuery):
    logging.info('Pressed from: ' + callback_query.message.chat.first_name + ', button: ' + callback_query.data)
    # в data у нас содержится текст callback_data
    data = callback_query.data
    if data == 'greetings':
        await greetings(callback_query.message)
    elif data == 'cat':
        await cat(callback_query.message)
    elif data == 'gif_cat':
        await catgif(callback_query.message)
    elif data == 'wiki':
        await wiki(callback_query.message)
    elif data == 'calc':
        await calc(callback_query.message)
    elif data == 'joke':
        await joke(callback_query.message)

# случайный анекдот
async def joke(message: types.Message, count = 2):
    response = requests.get("http://rzhunemogu.ru/RandJSON.aspx?CType=1")
    if response.status_code:
        try:
            data = json.loads(response.text, strict = False)
            await message.answer('Анекдот:\n' + data.get("content"))
        except Exception:
            if count > 0:
                return await joke(message, --count)
            logging.warning('Error parsing json from: http://rzhunemogu.ru, method: joke')
            await message.answer('Извините, неполадки на сервере, котики уже разбираются в чем проблема.')
    else:
        if count > 0:
            return await joke(message, --count)
        logging.warning('Request to: http://rzhunemogu.ru unavailable, from method: joke')
        await message.answer('Извините, база с анекдотами сейчас не доступна, котики пытаются починить все.')

# считаем математические выражения
async def calc(message: types.Message, regular = ""):
    if (not regular):
        await message.answer('Введите математическое выражение, например: 2+2*2, или (2+2)*2, или другое...')
    else:
        await message.answer(regular + ' = ' +numexpr.evaluate(regular))

# получаем статью из википедии
async def wiki(message: types.Message, word = ""):
    if (not word):
        word = wikipedia.random(1)
    result = wikipedia.search(word)
    try:
        page = wikipedia.page(result[0])
    except wikipedia.DisambiguationError as e:
        s = random.choice(e.options)
        page = wikipedia.page(s)
    summary = page.summary
    await message.answer(word + ' статья wiki:\n' + summary[:4000])

# выводим в отдельную функцию случайное приветствие пользователя
async def greetings(message: types.Message):
    hello_type = random.choice("Привет,Hi,Здравствуйте,Хай,Здарова".split(","))
    await message.answer(hello_type + ', ' + message.chat.first_name + ' !')

# отправляем с помощью сервиса cataas, фото котика
async def cat(message: types.Message):
    await bot.send_photo(message.chat.id, photo=f"https://cataas.com/cat?rand={random_string(16)}")

# отправить анимированного котика
async def catgif(message: types.Message):
    await bot.send_animation(message.chat.id, animation=f"https://cataas.com/cat/gif?rand={random_string(16)}")

# генерация строки из случайных символов заданной длины
def random_string(length):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

# Добавляем обработчик команды /start, который будет показывать наши главные кнопки
@dp.message(Command('start'))
async def cmd_start(message: types.Message):
    logging.info('Start command from: ' + message.chat.first_name)
    await bot.send_message(chat_id = message.chat.id, text = "Выберите действие: ", reply_markup = main_kb)

# здесь мы будем перехватать прочие сообщения от пользователя
@dp.message()
async def filter(message):
    logging.info('Received from: ' + message.chat.first_name + ', message: ' + message.text)
    if (any(message.text.lower().find(t) == 0 for t in "привет,hi,hello,здрасьте".split(","))):
        await greetings(message)
    elif (any(message.text.lower().find(t) == 0 for t in "котик,кот,кошка".split(","))):
        await cat(message)
    elif (any(message.text.lower().find(t) == 0 for t in "анекдот,шутка,прикол".split(","))):
        await joke(message)
    elif (any(message.text.lower().find(t) == 0 for t in "wiki,wikipedia,вики,википедиа".split(","))):
        await wiki(message)
    elif (re.compile(r'^[ 0-9+\-*/()]+$').match(message.text)):
        await calc(message, message.text)
    else:
        await wiki(message, message.text.lower())

async def main():
    # запускаем отслеживание сообщении для нашего бота
    await dp.start_polling(bot)

if __name__ == '__main__':
    # Асинхронно стартуем бот, чтобы он мог работать с группой людей
    asyncio.run(main())
