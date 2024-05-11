import sqlite3

# Создание и подключение к базе данных
conn = sqlite3.connect('custom.db')
c = conn.cursor()

# c.execute("DROP TABLE IF EXISTS user_tables")

# Создание таблицы для хранения списка таблиц, принадлежащих пользователям
c.execute('''CREATE TABLE IF NOT EXISTS user_tables
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT NOT NULL,
            user_table TEXT NOT NULL,
            table_description TEXT,
            table_columns TEXT,
            FOREIGN KEY (user) REFERENCES users(login))''')

# Функция для добавления новой таблицы, принадлежащей пользователю
def add_user_table(user_login, table_name, table_description, table_columns):
    c.execute("INSERT INTO user_tables (user, user_table, table_description, table_columns) VALUES (?, ?, ?, ?)", (user_login, table_name, table_description, table_columns))
    conn.commit()


# Сохранение и закрытие соединения с базой данных
conn.close()