import sqlite3
import os
import random
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import Command, CommandStart
import asyncio
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import logging

logger = logging.getLogger(__name__)

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()


# --- FSM: Состояния ---
class AddTaskStates(StatesGroup):
    waiting_for_task = State()


# --- Создание базы данных ---
def create_db():
    conn = sqlite3.connect('tasks.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task TEXT NOT NULL)''')
    conn.commit()
    conn.close()
    logger.info("База данных успешно создана или уже существует.")


create_db()


# --- /start ---
@dp.message(Command("start"))
async def cmd_start(message: Message):
    username = message.from_user.username if message.from_user.username else "Неизвестный пользователь"
    logger.info(f"Команда /start от пользователя @{username}")
    await message.answer("Привет! Я — твой бот-рандомайзер задач.\nНапиши /add чтобы добавить задачу.")


# --- /add ---
@dp.message(Command("add"))
async def cmd_add(message: Message, state: FSMContext):
    username = message.from_user.username if message.from_user.username else "Неизвестный пользователь"
    logger.info(f"Команда /add от пользователя @{username}")
    await message.answer("Пожалуйста, введите задачу.")
    await state.set_state(AddTaskStates.waiting_for_task)


# --- Получаем задачу от пользователя ---
@dp.message(AddTaskStates.waiting_for_task)
async def process_task(message: Message, state: FSMContext):
    task = message.text.strip()
    username = message.from_user.username if message.from_user.username else "Неизвестный пользователь"

    if not task:
        await message.answer("Пожалуйста, введите непустую задачу.")
        logger.warning(f"Пользователь @{username} пытался добавить пустую задачу.")
        return

    conn = sqlite3.connect('tasks.db')
    c = conn.cursor()
    c.execute("INSERT INTO tasks (task) VALUES (?)", (task,))
    conn.commit()
    conn.close()

    logger.info(f"Пользователь @{username} добавил задачу: {task}")
    await message.answer(f"Задача добавлена: {task}")
    await state.clear()


# --- /random ---
@dp.message(Command("random"))
async def cmd_random(message: Message):
    username = message.from_user.username if message.from_user.username else "Неизвестный пользователь"

    conn = sqlite3.connect('tasks.db')
    c = conn.cursor()
    c.execute("SELECT task FROM tasks")
    tasks = c.fetchall()
    conn.close()

    if tasks:
        task = random.choice(tasks)[0]
        logger.info(f"Пользователь @{username} запросил случайную задачу: {task}")
        await message.answer(f"Вот случайная задача: {task}")
    else:
        logger.warning(f"Пользователь @{username} запросил случайную задачу, но база пуста.")
        await message.answer("В базе пока нет задач.")


# --- Запуск бота ---
async def main():
    logger.info("Запуск бота...")
    await dp.start_polling(bot)