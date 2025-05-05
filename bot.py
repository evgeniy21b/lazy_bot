import sqlite3
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import Command
import asyncio

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()


# Функция для создания базы данных и таблицы
def create_db():
    conn = sqlite3.connect('tasks.db')
    c = conn.cursor()

    # Создание таблицы, если её нет
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task TEXT NOT NULL)''')

    conn.commit()
    conn.close()


# Вызов функции для создания базы данных
create_db()


@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Привет! Я — твой бот-рандомайзер задач.")


# Команда /add для начала добавления задачи
@dp.message(Command("add"))
async def cmd_add(message: Message):
    await message.answer("Пожалуйста, введите задачу и отправьте её.")


# Обработчик для ввода задачи (пользователь отправляет задачу после /add)
@dp.message()
async def add_task(message: Message):
    if message.text.startswith("/"):
        return  # Игнорируем команды

    task = message.text.strip()

    if task:
        # Подключаемся к базе данных
        conn = sqlite3.connect('tasks.db')
        c = conn.cursor()

        # Вставляем задачу в таблицу
        c.execute("INSERT INTO tasks (task) VALUES (?)", (task,))
        conn.commit()
        conn.close()

        await message.answer(f"Задача добавлена: {task}")
    else:
        await message.answer("Пожалуйста, введите задачу.")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
