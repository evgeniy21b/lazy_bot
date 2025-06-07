import sqlite3
from datetime import datetime
from tabulate import tabulate

def view_database():
    """Просмотр содержимого базы данных"""
    try:
        # Подключаемся к базе данных
        conn = sqlite3.connect('tasks.db')
        cursor = conn.cursor()

        # Получаем список всех таблиц
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        print("\n=== Содержимое базы данных ===\n")

        for table in tables:
            table_name = table[0]
            print(f"\n📋 Таблица: {table_name}")
            print("-" * 50)

            # Получаем структуру таблицы
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]

            # Получаем данные из таблицы
            cursor.execute(f"SELECT * FROM {table_name};")
            rows = cursor.fetchall()

            if rows:
                # Форматируем даты и статусы для лучшей читаемости
                formatted_rows = []
                for row in rows:
                    formatted_row = list(row)
                    for i, col in enumerate(columns):
                        if col[1] == 'created_at' and row[i]:
                            try:
                                # Пробуем преобразовать timestamp в читаемую дату
                                timestamp = float(row[i])
                                formatted_row[i] = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                            except (ValueError, TypeError):
                                # Если не получилось, оставляем как есть
                                formatted_row[i] = row[i]
                        elif col[1] == 'status' and row[i] is not None:
                            # Преобразуем статус в текст
                            formatted_row[i] = '✅ Выполнено' if row[i] else '⏳ В процессе'
                    formatted_rows.append(formatted_row)

                # Выводим данные в виде таблицы
                print(tabulate(formatted_rows, headers=column_names, tablefmt='grid'))
            else:
                print("Таблица пуста")

            print("\n" + "=" * 50)

        conn.close()

    except sqlite3.Error as e:
        print(f"Ошибка при работе с базой данных: {e}")
    except Exception as e:
        print(f"Произошла ошибка: {e}")

if __name__ == "__main__":
    view_database() 