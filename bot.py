import asyncio
import logging
from typing import Optional, Dict, Any
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.exceptions import TelegramAPIError
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime

from db_manager import DatabaseManager, Task

# Настройка логгера
logger = logging.getLogger("bot.main")

# Состояния FSM
class TaskStates(StatesGroup):
    """Состояния для создания и управления задачами"""
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_deletion = State()
    waiting_for_completion = State()

class BotManager:
    """Класс для управления ботом и обработки команд"""
    
    def __init__(self, token: str, db: DatabaseManager):
        """
        Инициализация бота
        
        Args:
            token: Токен бота
            db: Экземпляр менеджера базы данных
        """
        self.token = token
        self.bot = Bot(token=token)
        self.storage = MemoryStorage()
        self.dp = Dispatcher(storage=self.storage)
        self.db = db
        
        # Регистрируем обработчики команд
        self.dp.message.register(self.cmd_start, Command(commands=["start"]))
        self.dp.message.register(self.cmd_help, Command(commands=["help"]))
        self.dp.message.register(self.cmd_new, Command(commands=["new"]))
        self.dp.message.register(self.cmd_tasks, Command(commands=["tasks"]))
        self.dp.message.register(self.cmd_delete, Command(commands=["delete"]))
        self.dp.message.register(self.cmd_complete, Command(commands=["complete"]))
        
        # Регистрируем обработчики состояний
        self.dp.message.register(self.process_task_title, TaskStates.waiting_for_title)
        self.dp.message.register(self.process_task_description, TaskStates.waiting_for_description)
        
        # Регистрируем обработчик callback-запросов
        self.dp.callback_query.register(self.process_callback)
        
        logger.info("Бот инициализирован")

    async def cmd_start(self, message: types.Message) -> None:
        """Обработчик команды /start"""
        try:
            user_id = message.from_user.id
            username = message.from_user.username or message.from_user.first_name
            
            # Регистрируем пользователя
            self.db.add_user(user_id, username)
            logger.info(f"Зарегистрирован новый пользователь @{username} (ID: {user_id})")
            
            # Создаем клавиатуру
            builder = InlineKeyboardBuilder()
            builder.add(types.InlineKeyboardButton(
                text="📝 Создать задачу",
                callback_data="create_task"
            ))
            builder.add(types.InlineKeyboardButton(
                text="📋 Список задач",
                callback_data="list_tasks"
            ))
            builder.add(types.InlineKeyboardButton(
                text="❌ Удалить задачу",
                callback_data="delete_task"
            ))
            builder.add(types.InlineKeyboardButton(
                text="✅ Отметить как выполненную",
                callback_data="complete_task"
            ))
            builder.adjust(2)  # Размещаем кнопки по две в ряд
            
            await message.answer(
                f"👋 Привет, @{username}!\n\n"
                "Я бот для управления задачами. Вот что я умею:\n"
                "📝 Создавать новые задачи\n"
                "📋 Показывать список задач\n"
                "❌ Удалять задачи\n"
                "✅ Отмечать задачи как выполненные\n\n"
                "Выберите действие или используйте команды:\n"
                "/new - создать задачу\n"
                "/tasks - список задач\n"
                "/delete - удалить задачу\n"
                "/complete - отметить как выполненную\n"
                "/help - помощь",
                reply_markup=builder.as_markup()
            )
            logger.info(f"Пользователь @{username} запустил бота")
        except Exception as e:
            logger.error(f"Ошибка при обработке команды /start для пользователя {message.from_user.username}: {e}")
            await message.answer("❌ Произошла ошибка. Попробуйте позже.")
    
    async def cmd_help(self, message: types.Message) -> None:
        """Обработчик команды /help"""
        help_text = (
            "📚 Доступные команды:\n\n"
            "/start - Начать работу с ботом\n"
            "/new - Создать новую задачу\n"
            "/tasks - Показать список задач\n"
            "/delete - Удалить задачу\n"
            "/complete - Отметить задачу как выполненную\n"
            "/help - Показать это сообщение\n\n"
            "Для создания задачи:\n"
            "1. Нажмите 'Создать задачу' или используйте /new\n"
            "2. Введите название задачи\n"
            "3. Введите описание (или /skip для пропуска)"
        )
        await message.answer(help_text)
    
    async def cmd_new(self, message: types.Message, state: FSMContext) -> None:
        """Обработчик команды /new"""
        try:
            user_id = message.from_user.id
            username = message.from_user.username or message.from_user.first_name
            
            await state.set_state(TaskStates.waiting_for_title)
            await message.answer(
                "📝 Введите название задачи:",
                reply_markup=ReplyKeyboardRemove()
            )
            logger.info(f"Пользователь @{username} начал создание новой задачи")
        except Exception as e:
            logger.error(f"Ошибка при создании новой задачи: {e}")
            await message.answer("❌ Произошла ошибка. Попробуйте позже.")
    
    async def process_task_title(self, message: types.Message, state: FSMContext) -> None:
        """Обработчик ввода названия задачи"""
        try:
            user_id = message.from_user.id
            username = message.from_user.username or message.from_user.first_name
            title = message.text
            
            # Сохраняем название задачи
            task_id = self.db.add_task(user_id, title)
            logger.info(f"Создана новая задача с ID {task_id} для пользователя @{username}")
            
            # Переходим к вводу описания
            await state.set_state(TaskStates.waiting_for_description)
            await message.answer(
                "📄 Введите описание задачи (или /skip для пропуска):"
            )
        except Exception as e:
            logger.error(f"Ошибка при сохранении названия задачи: {e}")
            await message.answer("❌ Произошла ошибка. Попробуйте позже.")
            await state.clear()
    
    async def process_task_description(self, message: types.Message, state: FSMContext) -> None:
        """Обработчик ввода описания задачи"""
        try:
            user_id = message.from_user.id
            username = message.from_user.username or message.from_user.first_name
            
            if message.text == "/skip":
                description = None
            else:
                description = message.text
            
            # Получаем последнюю задачу пользователя
            cursor = self.db.conn.cursor()
            cursor.execute(
                "SELECT id FROM tasks WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
                (user_id,)
            )
            task_id = cursor.fetchone()[0]
            
            # Обновляем описание
            cursor.execute(
                "UPDATE tasks SET description = ? WHERE id = ? AND user_id = ?",
                (description, task_id, user_id)
            )
            self.db.conn.commit()
            
            logger.info(f"Добавлено описание к задаче {task_id} для пользователя @{username}")
            await message.answer("✅ Задача успешно создана!")
            await state.clear()
        except Exception as e:
            logger.error(f"Ошибка при сохранении описания задачи: {e}")
            await message.answer("❌ Произошла ошибка. Попробуйте позже.")
            await state.clear()
    
    async def cmd_tasks(self, message: Message):
        """Обработчик команды /tasks"""
        try:
            logger.info(f"Пользователь @{message.from_user.username} запросил список задач")
            tasks = self.db.get_user_tasks(message.from_user.id)
            
            if not tasks:
                await message.answer("У вас пока нет задач. Создайте новую с помощью команды /new")
                return
            
            response = "📋 Ваши задачи:\n\n"
            for task in tasks:
                task_id, title, description, created_at, status = task
                # Преобразуем строку даты в datetime объект
                created_date = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S").strftime("%d.%m.%Y %H:%M")
                status_emoji = "✅" if status else "⏳"
                response += f"{status_emoji} Задача #{task_id}\n"
                response += f"📌 {title}\n"
                if description:
                    response += f"📝 {description}\n"
                response += f"📅 Создана: {created_date}\n\n"
            
            await message.answer(response)
        except Exception as e:
            logger.error(f"Ошибка при получении списка задач: {e}")
            await message.answer("Произошла ошибка при получении списка задач. Попробуйте позже.")
    
    async def cmd_delete(self, message: types.Message) -> None:
        """Обработчик команды /delete"""
        try:
            user_id = message.from_user.id
            username = message.from_user.username or message.from_user.first_name
            
            # Получаем все задачи пользователя
            cursor = self.db.conn.cursor()
            cursor.execute(
                "SELECT id, title FROM tasks WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,)
            )
            tasks = cursor.fetchall()
            
            if not tasks:
                await message.answer("📝 У вас пока нет задач.")
                return
            
            # Создаем клавиатуру с задачами
            builder = InlineKeyboardBuilder()
            for task_id, title in tasks:
                builder.add(types.InlineKeyboardButton(
                    text=f"❌ {title}",
                    callback_data=f"delete_{task_id}"
                ))
            builder.adjust(1)  # Размещаем кнопки по одной в ряд
            
            await message.answer(
                "Выберите задачу для удаления:",
                reply_markup=builder.as_markup()
            )
            logger.info(f"Пользователь @{username} запросил удаление задачи")
        except Exception as e:
            logger.error(f"Ошибка при получении списка задач для удаления: {e}")
            await message.answer("❌ Произошла ошибка. Попробуйте позже.")
    
    async def cmd_complete(self, message: types.Message) -> None:
        """Обработчик команды /complete"""
        try:
            user_id = message.from_user.id
            username = message.from_user.username or message.from_user.first_name
            
            # Получаем незавершенные задачи пользователя
            cursor = self.db.conn.cursor()
            cursor.execute(
                "SELECT id, title FROM tasks WHERE user_id = ? AND status = 0 ORDER BY created_at DESC",
                (user_id,)
            )
            tasks = cursor.fetchall()
            
            if not tasks:
                await message.answer("✅ У вас нет незавершенных задач.")
                return
            
            # Создаем клавиатуру с задачами
            builder = InlineKeyboardBuilder()
            for task_id, title in tasks:
                builder.add(types.InlineKeyboardButton(
                    text=f"✅ {title}",
                    callback_data=f"complete_{task_id}"
                ))
            builder.adjust(1)  # Размещаем кнопки по одной в ряд
            
            await message.answer(
                "Выберите задачу для отметки о выполнении:",
                reply_markup=builder.as_markup()
            )
            logger.info(f"Пользователь @{username} запросил отметку о выполнении задачи")
        except Exception as e:
            logger.error(f"Ошибка при получении списка задач для отметки: {e}")
            await message.answer("❌ Произошла ошибка. Попробуйте позже.")
    
    async def process_callback(self, callback_query: CallbackQuery):
        """Обработчик callback-запросов от кнопок"""
        try:
            data = callback_query.data
            user_id = callback_query.from_user.id
            
            if data == "list_tasks":
                tasks = self.db.get_user_tasks(user_id)
                if not tasks:
                    await callback_query.message.answer("У вас пока нет задач. Создайте новую с помощью команды /new")
                    return
                
                response = "📋 Ваши задачи:\n\n"
                for task in tasks:
                    task_id, title, description, created_at, status = task
                    created_date = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S").strftime("%d.%m.%Y %H:%M")
                    status_emoji = "✅" if status else "⏳"
                    response += f"{status_emoji} Задача #{task_id}\n"
                    response += f"📌 {title}\n"
                    if description:
                        response += f"📝 {description}\n"
                    response += f"📅 Создана: {created_date}\n\n"
                
                await callback_query.message.answer(response)
            
            elif data == "delete_task":
                tasks = self.db.get_user_incomplete_tasks(user_id)
                if not tasks:
                    await callback_query.message.answer("У вас нет задач для удаления")
                    return
                
                keyboard = InlineKeyboardBuilder()
                for task_id, title in tasks:
                    keyboard.add(types.InlineKeyboardButton(
                        text=f"❌ {title}",
                        callback_data=f"delete_{task_id}"
                    ))
                
                await callback_query.message.answer(
                    "Выберите задачу для удаления:",
                    reply_markup=keyboard.as_markup()
                )
            
            elif data == "complete_task":
                tasks = self.db.get_user_incomplete_tasks(user_id)
                if not tasks:
                    await callback_query.message.answer("У вас нет незавершенных задач")
                    return
                
                keyboard = InlineKeyboardBuilder()
                for task_id, title in tasks:
                    keyboard.add(types.InlineKeyboardButton(
                        text=f"✅ {title}",
                        callback_data=f"complete_{task_id}"
                    ))
                
                await callback_query.message.answer(
                    "Выберите задачу для отметки о выполнении:",
                    reply_markup=keyboard.as_markup()
                )
            
            elif data.startswith("delete_"):
                task_id = int(data.split("_")[1])
                self.db.delete_task(task_id)
                logger.info(f"Пользователь @{callback_query.from_user.username} удалил задачу {task_id}")
                await callback_query.message.answer(f"✅ Задача #{task_id} удалена")
            
            elif data.startswith("complete_"):
                task_id = int(data.split("_")[1])
                self.db.complete_task(task_id)
                logger.info(f"Пользователь @{callback_query.from_user.username} отметил задачу {task_id} как выполненную")
                await callback_query.message.answer(f"✅ Задача #{task_id} отмечена как выполненная")
            
            await callback_query.answer()
            
        except Exception as e:
            logger.error(f"Ошибка при обработке callback-запроса: {e}")
            await callback_query.message.answer("Произошла ошибка. Попробуйте позже.")
            await callback_query.answer()
    
    async def run(self) -> None:
        """Запуск бота"""
        try:
            logger.info("Запуск бота...")
            await self.dp.start_polling(self.bot)
        except Exception as e:
            logger.error(f"Ошибка при запуске бота: {e}")
            raise

async def main(token: str) -> None:
    """
    Основная функция запуска бота
    
    Args:
        token: Токен Telegram бота
    """
    db = DatabaseManager()
    bot_manager = BotManager(token, db)
    await bot_manager.run()

if __name__ == "__main__":
    import asyncio
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("Токен бота не найден в переменных окружения")
    
    asyncio.run(main(token))