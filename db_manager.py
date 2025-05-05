import sqlite3

# Подключение к базе данных
conn = sqlite3.connect('tasks.db')
c = conn.cursor()

# Получаем все задачи из базы данных
c.execute("SELECT * FROM tasks")
tasks = c.fetchall()

# Выводим все задачи
for task in tasks:
    print(task)

# Закрываем соединение с базой данных
conn.close()
