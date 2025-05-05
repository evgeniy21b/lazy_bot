import asyncio
import logging
from aiogram.exceptions import TelegramNetworkError

# Импортируем функцию main из bot.py
from bot import main

# --- Настройка логгера ---
logging.basicConfig(
    filename="bot.log",          # Имя лог-файла
    level=logging.INFO,          # Уровень логирования
    format="%(asctime)s - %(levelname)s - %(message)s",  # Формат сообщений
    datefmt="%Y-%m-%d %H:%M:%S", # Формат даты/времени
    encoding='utf-8',            # Чтобы русские буквы не ломались
)

if __name__ == "__main__":
    try:
        logging.info("Бот запускается...")
        asyncio.run(main())
    except TelegramNetworkError as e:
        logging.error("🔌 Нет соединения с Telegram. Проверь интернет или VPN.")
        logging.exception(f"(подробнее: {e})")  # Запись полного исключения
        print("🔌 Нет соединения с Telegram. Проверь интернет или VPN.")
        print(f"(подробнее: {e})")
    except Exception as e:
        logging.error("❗Произошла неизвестная ошибка при запуске бота.")
        logging.exception(f"(подробнее: {e})")  # Запись полного исключения
        print("❗Произошла неизвестная ошибка при запуске бота.")
        print(f"(подробнее: {e})")
