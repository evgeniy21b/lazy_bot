import os
import sys
import logging
import asyncio
from dotenv import load_dotenv
from bot import BotManager
from db_manager import DatabaseManager

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

async def run_bot(token: str) -> None:
    """
    Запуск бота
    
    Args:
        token: Токен Telegram бота
    """
    try:
        # Инициализируем базу данных
        db = DatabaseManager()
        logger.info("База данных инициализирована")
        
        # Создаем и запускаем бота
        bot_manager = BotManager(token, db)
        logger.info("Бот запущен")
        await bot_manager.run()
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        raise

def main() -> None:
    """Основная функция"""
    try:
        # Загружаем переменные окружения
        load_dotenv()
        
        # Проверяем текущую директорию
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if os.getcwd() != current_dir:
            os.chdir(current_dir)
            logger.info(f"Изменена рабочая директория на {current_dir}")
        
        # Получаем токен бота
        token = os.getenv("BOT_TOKEN")
        if not token:
            raise ValueError("Токен бота не найден в переменных окружения")
        
        # Запускаем бота
        logger.info("Запуск бота...")
        asyncio.run(run_bot(token))
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
