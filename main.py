from flask import Flask, jsonify, request
import sqlite3

app = Flask(__name__)


##########################   пользователь   ###################################

# Функция для получения всех пользователей из базы данных
def get_all_users():
    conn = sqlite3.connect('custom.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    users = c.fetchall()
    conn.close()

    # Преобразование списка кортежей в список словарей
    users_list = []
    for user in users:
        user_dict = {
            "id": user[0],
            "login": user[1],
            "name": user[2],
            "password": user[3],
            "role": user[4]
        }
        users_list.append(user_dict)

    return users_list

# Маршрут для возврата всех пользователей
@app.route('/users', methods=['GET'])
def users():
    users = get_all_users()
    return jsonify(users)



# Функция для создания нового пользователя
def create_user(login, name, password, role):
    conn = sqlite3.connect('custom.db')
    c = conn.cursor()

    # Проверка наличия пользователя с таким логином
    c.execute("SELECT * FROM users WHERE login = ?", (login,))
    existing_user = c.fetchone()
    if existing_user:
        conn.close()
        return "close"

    # Вставляем нового пользователя в таблицу
    c.execute("INSERT INTO users (login, name, password, role) VALUES (?, ?, ?, ?)", (login, name, password, role))
    conn.commit()
    conn.close()

    # Возвращаем информацию о созданном пользователе
    return {
        "id": c.lastrowid,
        "login": login,
        "name": name,
        "role": role
    }

# Маршрут для создания нового пользователя
@app.route('/users', methods=['POST'])
def create_new_user():
    data = request.get_json()
    login = data.get('login')
    name = data.get('name')
    password = data.get('password')
    role = data.get('role')

    if not login or not name or not password or not role:
        return jsonify({"error": "Missing required fields"}), 400

    user = create_user(login, name, password, role)
    if user != 'close':
        return jsonify(user), 201
    return jsonify({"error": "User has been"}), 400


# Функция для аутентификации пользователя
def authenticate_user(login, password):
    conn = sqlite3.connect('custom.db')
    c = conn.cursor()
    c.execute("SELECT id, login, password, name, role FROM users WHERE login = ?", (login,))
    user_data = c.fetchone()
    conn.close()

    if user_data and (password == user_data[2]):
        return {
            "id": user_data[0],
            "login": user_data[1],
            "name": user_data[3],
            "role":user_data[4]
        }
    return None

# Маршрут для аутентификации пользователя
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    login = data.get('login')
    password = data.get('password')

    if not login or not password:
        return jsonify({"error": "Missing required fields"}), 400

    user = authenticate_user(login, password)
    if user:
        return jsonify(user), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401



#########################     таблица с названиями таблиц для пользователя       ###################################

# Функция для получения списка всех таблиц, их полей и данных
def get_all_tables_and_data():
    conn = sqlite3.connect('custom.db')
    c = conn.cursor()

    # Получаем список всех таблиц
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    all_tables = [row[0] for row in c.fetchall()]

    # Получаем список полей и данные для каждой таблицы
    tables_and_data = {}
    for table_name in all_tables:
        # Получаем список полей
        c.execute(f"PRAGMA table_info({table_name})")
        table_fields = [row[1] for row in c.fetchall()]

        # Получаем данные из таблицы
        c.execute(f"SELECT * FROM {table_name}")
        table_rows = [dict(zip(table_fields, row)) for row in c.fetchall()]

        tables_and_data[table_name] = {
            "fields": table_fields,
            "data": table_rows
        }

    conn.close()
    return tables_and_data

# Маршрут для получения списка всех таблиц, их полей и данных
@app.route('/all_tables', methods=['GET'])
def all_tables():
    tables_and_data = get_all_tables_and_data()
    return jsonify(tables_and_data)





# Функция для получения всех записей из таблицы user_tables
def get_all_user_tables():
    conn = sqlite3.connect('custom.db')
    c = conn.cursor()
    c.execute("SELECT * FROM user_tables")
    user_tables = c.fetchall()
    conn.close()

    # Преобразование списка кортежей в список словарей
    user_tables_list = []
    for table in user_tables:
        table_dict = {
            "id": table[0],
            "user": table[1],
            "user_table": table[2],
            "table_description": table[3],
            "table_columns": table[4]
        }
        user_tables_list.append(table_dict)

    return user_tables_list

# Маршрут для получения всех записей из таблицы user_tables
@app.route('/user_tables', methods=['GET'])
def all_user_tables():
    user_tables = get_all_user_tables()
    return jsonify(user_tables)





# Функция для получения всех таблиц, принадлежащих пользователю
def get_user_tables(user_login):
    conn = sqlite3.connect('custom.db')
    c = conn.cursor()
    c.execute("SELECT * FROM user_tables WHERE user = ?", (user_login,))
    user_tables = c.fetchall()
    conn.close()

    # Преобразование списка кортежей в список словарей
    user_tables_list = []
    for table in user_tables:
        table_dict = {
            "id": table[0],
            "user": table[1],
            "user_table": table[2],
            "table_description": table[3],
            "table_columns": table[4]
        }
        user_tables_list.append(table_dict)

    return user_tables_list

# Маршрут для получения всех таблиц, принадлежащих пользователю
@app.route('/user_tables/<string:user_login>', methods=['GET'])
def user_tables(user_login):
    user_tables = get_user_tables(user_login)
    return jsonify(user_tables)



###############################    создание таблиц    #############################################



# Функция для создания новой таблицы, принадлежащей пользователю
def create_user_table(user_login, table_name, table_description, table_columns):
    conn = sqlite3.connect('custom.db')
    c = conn.cursor()

    # Проверяем, существует ли уже таблица с таким именем
    c.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    table_exists = c.fetchone()[0] > 0

    if not table_exists:
        # Создаем новую таблицу
        create_table_query = f"CREATE TABLE {table_name} ({table_columns})"
        c.execute(create_table_query)

        # Добавляем запись в таблицу user_tables
        c.execute("INSERT INTO user_tables (user, user_table, table_description, table_columns) VALUES (?, ?, ?, ?)", (user_login, table_name, table_description, table_columns))
        conn.commit()

        # Возвращаем информацию о созданной таблице
        return {
            "user": user_login,
            "user_table": table_name,
            "table_description": table_description,
            "table_columns": table_columns
        }
    else:
        # Возвращаем ошибку, если таблица уже существует
        return {"error": f"Table '{table_name}' already exists."}, 400

# Маршрут для создания новой таблицы, принадлежащей пользователю
@app.route('/user_tables', methods=['POST'])
def create_new_user_table():
    data = request.get_json()
    user_login = data.get('user')
    table_name = data.get('user_table')
    table_description = data.get('table_description')
    table_columns = data.get('table_columns')

    if not user_login or not table_name or not table_description or not table_columns:
        return jsonify({"error": "Missing required fields"}), 400

    new_table = create_user_table(user_login, table_name, table_description, table_columns)
    return jsonify(new_table), 201




# Функция для получения всех таблиц и их содержимое по пользователю
def get_user_tables_and_data(user_login):
    conn = sqlite3.connect('custom.db')
    c = conn.cursor()

    # Получаем список всех таблиц, принадлежащих пользователю
    c.execute("SELECT user_table FROM user_tables WHERE user = ?", (user_login,))
    user_tables = [row[0] for row in c.fetchall()]

    # Получаем содержимое каждой таблицы
    tables_and_data = {}
    for user_table in user_tables:
        # Получаем список полей
        a = c.execute(f"PRAGMA table_info({user_table})")
        table_fields = [row[1] for row in c.fetchall()]
        # Получаем данные из таблицы
        c.execute(f"SELECT * FROM {user_table}")
        table_rows = [dict(zip(table_fields, row)) for row in c.fetchall()]
        tables_and_data[user_table] = {
            "fields": table_fields,
            "data": table_rows
        }

    conn.close()
    return tables_and_data

# Маршрут для получения всех таблиц и их содержимое по пользователю
@app.route('/user_tables_table/<string:user_login>', methods=['GET'])
def user_tables_table(user_login):
    tables_and_data = get_user_tables_and_data(user_login)
    return jsonify(tables_and_data)




# Функция для удаления записи из таблицы user_tables по названию таблицы
def delete_user_table(user_login, table_name):
    conn = sqlite3.connect('custom.db')
    c = conn.cursor()

    # Удаляем запись из таблицы user_tables
    c.execute("DELETE FROM user_tables WHERE user = ? AND user_table = ?", (user_login, table_name))
    conn.commit()

    # Удаляем саму таблицу
    c.execute(f"DROP TABLE IF EXISTS {table_name}")
    conn.commit()

    conn.close()
    return {"message": f"Table '{table_name}' has been deleted."}

# Маршрут для удаления таблицы по названию
@app.route('/user_tables/<string:user_login>/<string:table_name>', methods=['DELETE'])
def delete_table(user_login, table_name):
    result = delete_user_table(user_login, table_name)
    return jsonify(result), 200


# изменение колонок и работа с данными таблицы ########################################

# Функция для добавления колонок в таблицу по пользователю
def add_columns_to_table(user_login, table_name, columns):
    conn = sqlite3.connect('custom.db')
    c = conn.cursor()

    # Получаем текущие колонки таблицы
    c.execute(f"PRAGMA table_info({table_name})")
    existing_columns = [row[1] for row in c.fetchall()]

    # Определяем новые колонки, которые еще не существуют
    new_columns = [column for column in columns if column not in existing_columns]

    if not new_columns:
        conn.close()
        return {"message": "No new columns to add."}

    # Добавляем новые колонки в таблицу
    for column in new_columns:
        c.execute(f"ALTER TABLE {table_name} ADD COLUMN {column}")
    conn.commit()

    conn.close()
    return {"message": f"New columns {', '.join(new_columns)} have been added to table '{table_name}'."}

# Маршрут для добавления колонок в таблицу по пользователю
@app.route('/add_columns/<string:user_login>/<string:table_name>', methods=['POST'])
def add_columns(user_login, table_name):
    data = request.get_json()
    columns = data.get('columns', [])

    result = add_columns_to_table(user_login, table_name, columns)
    return jsonify(result), 200



# Функция для удаления колонок из таблицы по пользователю
def drop_columns_from_table(user_login, table_name, columns):
    conn = sqlite3.connect('custom.db')
    c = conn.cursor()

    # Получаем текущие колонки таблицы
    c.execute(f"PRAGMA table_info({table_name})")
    existing_columns = [row[1] for row in c.fetchall()]

    # Определяем колонки, которые не существуют в таблице
    non_existing_columns = [column for column in columns if column not in existing_columns]

    if non_existing_columns:
        conn.close()
        return {"message": f"Columns {', '.join(non_existing_columns)} do not exist in table '{table_name}'."}

    # Удаляем указанные колонки из таблицы
    for column in columns:
        c.execute(f"ALTER TABLE {table_name} DROP COLUMN {column}")
    conn.commit()

    conn.close()
    return {"message": f"Columns {', '.join(columns)} have been dropped from table '{table_name}'."}

# Маршрут для удаления колонок из таблицы по пользователю
@app.route('/drop_columns/<string:user_login>/<string:table_name>', methods=['DELETE'])
def drop_columns(user_login, table_name):
    data = request.get_json()
    columns = data.get('columns', [])

    result = drop_columns_from_table(user_login, table_name, columns)
    return jsonify(result), 200



# Функция для добавления данных в столбцы таблицы
def add_data_to_table(user_login, table_name, data):
    conn = sqlite3.connect('custom.db')
    c = conn.cursor()

    # Формируем строку для вставки данных
    placeholders = ', '.join(['?'] * len(data))
    columns = ', '.join(data.keys())
    values = tuple(data.values())

    # Вставляем данные в таблицу
    c.execute(f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})", values)
    conn.commit()

    conn.close()
    return {"message": "Data has been added to the table."}

# Маршрут для добавления данных в столбцы таблицы
@app.route('/add_data/<string:user_login>/<string:table_name>', methods=['POST'])
def add_data(user_login, table_name):
    data = request.get_json()
    
    result = add_data_to_table(user_login, table_name, data)
    return jsonify(result), 200






# Функция для изменения данных в таблице по ID
def update_data_by_id(user_login, table_name, id, new_data):
    conn = sqlite3.connect('custom.db')
    c = conn.cursor()

    # Формируем строку для обновления данных
    set_values = ', '.join([f"{key} = ?" for key in new_data.keys()])
    values = tuple(new_data.values())

    # Обновляем данные в таблице по ID
    c.execute(f"UPDATE {table_name} SET {set_values} WHERE id = ?", values + (id,))
    conn.commit()

    conn.close()
    return {"message": f"Data with ID {id} has been updated in the table '{table_name}'."}

# Маршрут для изменения данных в таблице по ID
@app.route('/update_data/<string:user_login>/<string:table_name>/<int:id>', methods=['PUT'])
def update_data(user_login, table_name, id):
    new_data = request.get_json()
    
    result = update_data_by_id(user_login, table_name, id, new_data)
    return jsonify(result), 200



# Функция для удаления данных из таблицы по ID
def delete_data_by_id(user_login, table_name, id):
    conn = sqlite3.connect('custom.db')
    c = conn.cursor()

    # Удаляем данные из таблицы по ID
    c.execute(f"DELETE FROM {table_name} WHERE id = ?", (id,))
    conn.commit()

    conn.close()
    return {"message": f"Data with ID {id} has been deleted from the table '{table_name}'."}

# Маршрут для удаления данных из таблицы по ID
@app.route('/delete_data/<string:user_login>/<string:table_name>/<int:id>', methods=['DELETE'])
def delete_data(user_login, table_name, id):
    result = delete_data_by_id(user_login, table_name, id)
    return jsonify(result), 200


if __name__ == '__main__':
    app.run(debug=True)