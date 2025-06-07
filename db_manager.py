import sqlite3
import logging
from typing import List, Tuple, Optional, Any
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class Task:
    """Класс для представления задачи"""
    id: Optional[int]
    title: str
    description: str
    created_at: datetime
    status: str
    user_id: int

class DatabaseManager:
    """Класс для управления базой данных"""
    
    def __init__(self, db_path: str = "tasks.db"):
        """
        Инициализация менеджера базы данных
        
        Args:
            db_path: Путь к файлу базы данных
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
        logger.info(f"База данных инициализирована: {db_path}")
    
    def _create_tables(self) -> None:
        """Создание необходимых таблиц в базе данных"""
        cursor = self.conn.cursor()
        
        # Создаем таблицу пользователей
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Создаем таблицу задач
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        self.conn.commit()
        logger.info("Таблицы созданы")
    
    def add_user(self, user_id: int, username: str) -> None:
        """
        Добавление нового пользователя
        
        Args:
            user_id: ID пользователя в Telegram
            username: Имя пользователя
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
                (user_id, username)
            )
            self.conn.commit()
            logger.info(f"Пользователь {username} добавлен в базу данных")
        except Exception as e:
            logger.error(f"Ошибка при добавлении пользователя: {e}")
            raise
    
    def add_task(self, user_id: int, title: str, description: str = None) -> int:
        """
        Добавление новой задачи
        
        Args:
            user_id: ID пользователя
            title: Название задачи
            description: Описание задачи (опционально)
            
        Returns:
            int: ID созданной задачи
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO tasks (user_id, title, description) VALUES (?, ?, ?)",
                (user_id, title, description)
            )
            self.conn.commit()
            task_id = cursor.lastrowid
            logger.info(f"Задача {task_id} добавлена для пользователя {user_id}")
            return task_id
        except Exception as e:
            logger.error(f"Ошибка при добавлении задачи: {e}")
            raise
    
    def get_user_tasks(self, user_id: int) -> list:
        """
        Получение всех задач пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            list: Список задач пользователя
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT id, title, description, created_at, status FROM tasks WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,)
            )
            tasks = cursor.fetchall()
            logger.info(f"Получено {len(tasks)} задач для пользователя {user_id}")
            return tasks
        except Exception as e:
            logger.error(f"Ошибка при получении задач пользователя: {e}")
            raise
    
    def get_user_incomplete_tasks(self, user_id: int) -> list:
        """
        Получение незавершенных задач пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            list: Список незавершенных задач пользователя
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT id, title FROM tasks WHERE user_id = ? AND status = 0 ORDER BY created_at DESC",
                (user_id,)
            )
            tasks = cursor.fetchall()
            logger.info(f"Получено {len(tasks)} незавершенных задач для пользователя {user_id}")
            return tasks
        except Exception as e:
            logger.error(f"Ошибка при получении незавершенных задач пользователя: {e}")
            raise
    
    def complete_task(self, task_id: int) -> None:
        """
        Отметка задачи как выполненной
        
        Args:
            task_id: ID задачи
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE tasks SET status = 1 WHERE id = ?",
                (task_id,)
            )
            self.conn.commit()
            logger.info(f"Задача {task_id} отмечена как выполненная")
        except Exception as e:
            logger.error(f"Ошибка при отметке задачи как выполненной: {e}")
            raise
    
    def delete_task(self, task_id: int) -> None:
        """
        Удаление задачи
        
        Args:
            task_id: ID задачи
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "DELETE FROM tasks WHERE id = ?",
                (task_id,)
            )
            self.conn.commit()
            logger.info(f"Задача {task_id} удалена")
        except Exception as e:
            logger.error(f"Ошибка при удалении задачи: {e}")
            raise
    
    def __del__(self):
        """Закрытие соединения с базой данных при удалении объекта"""
        if hasattr(self, 'conn'):
            self.conn.close()
            logger.info("Соединение с базой данных закрыто")
