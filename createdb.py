import sqlite3

# Создание и подключение к базе данных
conn = sqlite3.connect('custom.db')
conn.close()
