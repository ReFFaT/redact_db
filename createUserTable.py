import sqlite3

# Создание и подключение к базе данных
conn = sqlite3.connect('custom.db')
c = conn.cursor()

# Создание таблицы пользователей с полем "логин"
c.execute('''CREATE TABLE IF NOT EXISTS users
             (id INTEGER PRIMARY KEY AUTOINCREMENT, 
              login TEXT NOT NULL,
              name TEXT NOT NULL, 
              password TEXT NOT NULL, 
              role TEXT NOT NULL)''')

# Функция для добавления тестовых пользователей
def add_test_users():
    # Пользователь с ролью "admin"
    c.execute("INSERT INTO users (login, name, password, role) VALUES (?, ?, ?, ?)", ("admin_user", "Admin User", "admin_password", "admin"))

    # Пользователь с ролью "user"
    c.execute("INSERT INTO users (login, name, password, role) VALUES (?, ?, ?, ?)", ("regular_user", "Regular User", "user_password", "user"))

    conn.commit()

# Добавление тестовых пользователей
# add_test_users()

# Сохранение и закрытие соединения с базой данных
conn.close()