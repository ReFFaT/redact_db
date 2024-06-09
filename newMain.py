from flask import Flask, jsonify, request, send_file
import sqlite3
from flask_cors import CORS
import pandas as pd
import os
import tempfile
app = Flask(__name__)
CORS(app)

# Подключение к базе данных
def get_db_connection():
    conn = sqlite3.connect('all_users.db')
    conn.row_factory = sqlite3.Row
    return conn


# Получение списка всех пользователей
@app.route('/users', methods=['GET'])
def get_users():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    users = c.fetchall()
    conn.close()
    return jsonify([dict(user) for user in users])

# Создание нового пользователя
@app.route('/users', methods=['POST'])
def create_user():
    login = request.json['login']
    name = request.json['name']
    role = request.json['role']
    password = request.json['password']
    # Проверка, есть ли уже пользователь с таким логином
    conn = sqlite3.connect('all_users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE login = ?", (login,))
    user = c.fetchone()
    conn.close()
    
    if user:
        return jsonify({'error': 'User already exists'}), 400
    
    # Создание новой базы данных с логином пользователя
    new_db_name = f"{login}.db"
    try:
        new_conn = sqlite3.connect(new_db_name)
        new_c = new_conn.cursor()
        
        # Создание таблицы user_tables
        new_c.execute('''CREATE TABLE IF NOT EXISTS user_tables
                        (tables TEXT, description TEXT)''')
        
        new_conn.commit()
        new_conn.close()
        
        # Сохранение пользователя в таблице users
        conn = sqlite3.connect('all_users.db')
        c = conn.cursor()
        c.execute("INSERT INTO users (login, name, role, db_list, password) VALUES (?, ?, ?, ?, ?)", (login, name, role, new_db_name, password))
        conn.commit()
        user_id = c.lastrowid
        conn.close()
        
        # Возвращение всех полей, кроме пароля
        return jsonify({
            'id': user_id,
            'login': login,
            'name': name,
            'role': role,
            'tables': ''
        }), 201
    except sqlite3.Error as e:
        print(f"Error occurred: {e}")
        return jsonify({'error': 'Failed to create user'}), 500



# Маршрут для получения пользователя по логину
@app.route('/user/<string:login>', methods=['GET'])
def get_user(login):
    conn = sqlite3.connect('all_users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE login = ?", (login,))
    user = c.fetchone()
    conn.close()
    
    if user:
        return jsonify({
            'id': user[0],
            'login': user[1],
            'name': user[2],
            'role': user[3],
            'db_list': user[4]
        })
    else:
        return jsonify({'error': 'User not found'}), 404


# Авторизация пользователя
@app.route('/login', methods=['POST'])
def login():
    login = request.json['login']
    password = request.json['password']
    
    # Проверка логина и пароля
    conn = sqlite3.connect('all_users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE login = ? AND password = ?", (login, password))
    user = c.fetchone()
    conn.close()
    
    if user:
        print(user)
        # Возвращение всех полей, кроме пароля
        return jsonify({
            'id': user[0],
            'login': user[1],
            'name': user[2],
            'role': user[3],
            'db_list': user[4]
        })
    else:
        return jsonify({'error': 'Invalid login or password'}), 401

# Удаление пользователя
@app.route('/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    conn = sqlite3.connect('all_users.db')
    c = conn.cursor()
    
    # Получение списка баз данных пользователя из колонки db_list
    try:
        c.execute("SELECT db_list FROM users WHERE id = ?", (id,))
        db_list = c.fetchone()[0]
    except:
        print(f"Error occurred: {e}")
        return jsonify({'error': 'Failed to create user'}), 500
    if len(db_list)<1: 
        return jsonify({'message': 'Ошибка при удалении'}), 400
    # Удаление баз данных пользователя
    for db_name in db_list.split(','):
        try:
            os.remove(db_name)
        except OSError as e:
            print(f"Error occurred: {e}")
            return jsonify({'error': 'Failed to delete user'}), 500
    
    # Удаление пользователя из таблицы users
    c.execute("DELETE FROM users WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'User deleted'}), 200


# ################################# создание получение редактирование удаление таблиц #########################################


# Маршрут для создания новой таблицы, принадлежащей пользователю
@app.route('/user_tables', methods=['POST'])
def create_new_user_table():
    data = request.get_json()
    user_login = data.get('user')
    table_name = data.get('table_name')
    table_description = data.get('table_description')

    if not user_login or not table_name or not table_description:
        return jsonify({"error": "Missing required fields"}), 400

    # Открываем базу данных по логину
    conn = sqlite3.connect(f"{user_login}.db")
    c = conn.cursor()

    # Проверяем, есть ли уже таблица с указанным именем
    c.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    table_exists = c.fetchone()[0] > 0

    if table_exists:
        return jsonify({"error": "Table already exists"}), 400

    # Создаем новую таблицу
    create_table_query = f"CREATE TABLE {table_name} (id INTEGER PRIMARY KEY AUTOINCREMENT)"
    c.execute(create_table_query)

    # Добавляем запись в таблицу user_tables
    c.execute("INSERT INTO user_tables (tables, description) VALUES (?, ?)", (table_name, table_description))
    conn.commit()

    # Возвращаем информацию о созданной таблице
    return jsonify({
        "user": user_login,
        "table_name": table_name,
        "table_description": table_description
    }), 201

# Функция для получения всех таблиц, принадлежащих пользователю
def get_user_tables(user_login):
    user_db=f'{user_login}.db'
    conn = sqlite3.connect(user_db)
    c = conn.cursor()
    c.execute("SELECT * FROM user_tables")
    user_tables = c.fetchall()
    

    # Преобразование списка кортежей в список словарей
    user_tables_list = []
    for table in user_tables:
        table_dict = {
            "tables": table[0],
            "description": table[1]
        }

        # Получение количества записей в таблице
        c.execute(f"SELECT COUNT(*) FROM {table[0]}")
        table_dict['record_count'] = c.fetchone()[0]

        # Получение списка колонок в таблице
        c.execute(f"PRAGMA table_info({table[0]})")
        table_dict['columns'] = [row[1] for row in c.fetchall()]

        user_tables_list.append(table_dict)
    conn.close()

    return user_tables_list

# Маршрут для получения всех таблиц, принадлежащих пользователю
@app.route('/user_tables/<string:user_login>', methods=['GET'])
def user_tables(user_login):
    user_tables = get_user_tables(user_login)
    return jsonify(user_tables)



# Маршрут для удаления таблицы и записи о ней в таблице user_tables
@app.route('/tables/<string:user>/<string:table_name>', methods=['DELETE'])
def delete_table(user,table_name):
    try:
        user_login = user
        user_db = f'{user_login}.db'
        conn = sqlite3.connect(user_db)
        c = conn.cursor()

        # Удаление записи о таблице в таблице user_tables
        c.execute("DELETE FROM user_tables WHERE tables = ?", (table_name,))
        conn.commit()

        # Удаление таблицы
        c.execute(f"DROP TABLE {table_name}")
        conn.commit()

        conn.close()

        return jsonify({'message': 'Table and record deleted'}), 200
    except:
        return jsonify({'message': 'Не удалось удалить таблицу'}), 400



@app.route('/export', methods=['POST'])
def export_table():
    data = request.json
    db_name = data.get('db_name')
    user_db=f'{db_name}.db'

    table_name = data.get('table')

    if not user_db or not table_name:
        return jsonify({"error": "Database name and table name are required"}), 400

    # Query to get all data from the specified table
    query = f"SELECT * FROM {table_name}"
    conn = sqlite3.connect(user_db)
    df = pd.read_sql_query(query, conn)
    conn.close()

    # Save DataFrame to a temporary Excel file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
        df.to_excel(tmp.name, index=False)
        tmp_path = tmp.name

    # Send the temporary file and ensure it's deleted after sending
    response = send_file(tmp_path, as_attachment=True)
    response.call_on_close(lambda: os.remove(tmp_path))

    return response

# ################################# работа с колонками таблицы #########################################

# Функция для получения данных таблицы
def get_table_data(db_name, table_name):
    db=f'{db_name}.db'
    conn = sqlite3.connect(db)
    c = conn.cursor()

    # Получаем список полей и их типов
    c.execute(f"PRAGMA table_info({table_name})")
    table_fields = []
    for row in c.fetchall():
        column_name = row[1]
        column_type = row[2] if row[2] else "UNKNOWN"
        table_fields.append(f"{column_name}_{column_type}")

    # Получаем данные из таблицы
    c.execute(f"SELECT * FROM {table_name}")
    table_rows = [dict(zip([field.split('_')[0] for field in table_fields], row)) for row in c.fetchall()]

    conn.close()
    return table_fields, table_rows

# Маршрут для получения данных таблицы
@app.route('/table_data/<string:db_name>/<string:table_name>', methods=['GET'])
def table_data(db_name, table_name):
    table_fields, table_rows = get_table_data(db_name, table_name)
    return jsonify({
        "fields": table_fields,
        "data": table_rows
    })


# Функция для добавления колонок в таблицу
def add_columns_to_table(db_name, table_name, columns):
    db=f'{db_name}.db'
    conn = sqlite3.connect(db)
    c = conn.cursor()

    # Получаем текущие колонки таблицы
    c.execute(f"PRAGMA table_info({table_name})")
    existing_columns = [row[1] for row in c.fetchall()]

    # Определяем новые колонки, которые еще не существуют
    new_columns = [column for column in columns if column['col'] not in existing_columns]

    if not new_columns:
        conn.close()
        return {"message": "No new columns to add."}

    # Добавляем новые колонки в таблицу
    for column in new_columns:
        col_name = column['col']
        col_type = column['type']  # Если тип не указан, то будет пустая строка
        if col_type:
            c.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}")
        else:
            c.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_name}")
    conn.commit()

    conn.close()
    return {"message": f"New columns {', '.join([col['col'] for col in new_columns])} have been added to table '{table_name}'."}

# Маршрут для добавления колонок в таблицу
@app.route('/add_columns', methods=['POST'])
def add_columns():
    data = request.get_json()
    db_name = data.get('db_name')
    table_name = data.get('table_name')
    columns = data.get('columns', [])

    result = add_columns_to_table(db_name, table_name, columns)
    return jsonify(result), 200




# Функция для удаления колонки из таблицы
def drop_column_from_table(db_name, table_name, column_name):
    try:
        db=f'{db_name}.db'
        conn = sqlite3.connect(db)
        c = conn.cursor()

        # Удаляем указанную колонку из таблицы
        c.execute(f"ALTER TABLE {table_name} DROP COLUMN {column_name}")
        conn.commit()

        conn.close()
        return jsonify({"message": f"Column '{column_name}' has been dropped from table '{table_name}'."}),200
    except: 
        return jsonify({"message": "Не удалось удалить столбец"}),400

# Маршрут для удаления колонки из таблицы
@app.route('/drop_column/<string:db_name>/<string:table_name>/<string:column_name>', methods=['DELETE'])
def drop_column(db_name,table_name,column_name):
    # data = request.get_json()
    # db_name = data.get('db_name')
    # table_name = data.get('table_name')
    # column_name = data.get('column_name')

    return drop_column_from_table(db_name, table_name, column_name)




# Функция для изменения названия колонки
def rename_column_in_table(db_name, table_name, old_column_name, new_column_name):
    try:
        db=f'{db_name}.db'
        conn = sqlite3.connect(db)
        c = conn.cursor()

        # Изменяем название колонки
        c.execute(f"ALTER TABLE {table_name} RENAME COLUMN {old_column_name} TO {new_column_name}")
        conn.commit()

        conn.close()
        return jsonify ({"message": f"Column '{old_column_name}' has been renamed to '{new_column_name}' in table '{table_name}'."}), 200
    except:
        return jsonify({"message": "Не удалось изменить название столбца"}), 400
# Маршрут для изменения названия колонки
@app.route('/rename_column', methods=['PUT'])
def rename_column():
    data = request.get_json()
    db_name = data.get('db_name')
    table_name = data.get('table_name')
    old_column_name = data.get('old_column_name')
    new_column_name = data.get('new_column_name')

    return rename_column_in_table(db_name, table_name, old_column_name, new_column_name)


# ################################# работа с данными таблицы #########################################



# Функция для добавления данных в столбцы таблицы
def add_data_to_table(db_name, table_name, data):
    try:
        db=f'{db_name}.db'
        conn = sqlite3.connect(db)
        c = conn.cursor()

        # Формируем строку для вставки данных
        placeholders = ', '.join(['?'] * len(data))
        columns = ', '.join(data.keys())
        values = tuple(data.values())

        # Вставляем данные в таблицу
        c.execute(f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})", values)
        conn.commit()

        conn.close()
        return jsonify({"message": "Data has been added to the table."}), 200
    except:
        return jsonify({"message": "Не удалось добавить данные."}), 400

# Маршрут для добавления данных в столбцы таблицы
@app.route('/add_data', methods=['POST'])
def add_data():
    data = request.get_json()
    db_name = data.get('db_name')
    table_name = data.get('table_name')
    data_to_add = data.get('data')

    return add_data_to_table(db_name, table_name, data_to_add)




# Функция для изменения данных в таблице по ID
def update_data_by_id(db_name, table_name, id, new_data):
    try:
        db=f'{db_name}.db'
        conn = sqlite3.connect(db)
        c = conn.cursor()

        # Формируем строку для обновления данных
        set_values = ', '.join([f"{key} = ?" for key in new_data.keys()])
        values = tuple(new_data.values())

        # Обновляем данные в таблице по ID
        c.execute(f"UPDATE {table_name} SET {set_values} WHERE id = ?", values + (id,))
        conn.commit()

        conn.close()
        return jsonify({"message": f"Data with ID {id} has been updated in the table '{table_name}'."}), 200
    except:
        return jsonify({"message": "Не удалось изменить данные"}), 400


# Маршрут для изменения данных в таблице по ID
@app.route('/update_data', methods=['PUT'])
def update_data():
    data = request.get_json()
    db_name = data.get('db_name')
    table_name = data.get('table_name')
    id = data.get('id')
    new_data = data.get('new_data')

    return update_data_by_id(db_name, table_name, id, new_data)



# Функция для удаления данных из таблицы по ID
def delete_data_by_id(db_name, table_name, id):
    try:
        db=f'{db_name}.db'
        conn = sqlite3.connect(db)
        c = conn.cursor()

        # Удаляем данные из таблицы по ID
        c.execute(f"DELETE FROM {table_name} WHERE id = ?", (id,))
        conn.commit()

        conn.close()
        return jsonify({"message": f"Data with ID {id} has been deleted from the table '{table_name}'."}),200
    except:
        return jsonify({"message": "Не удалось удалить данные"}),400



# Маршрут для удаления данных из таблицы по ID
@app.route('/delete_data', methods=['DELETE'])
def delete_data():
    data = request.get_json()
    db_name = data.get('db_name')
    table_name = data.get('table_name')
    id = data.get('id')

    return delete_data_by_id(db_name, table_name, id)


# Маршрут для поиска в таблице по указанному столбцу и значению
@app.route('/search-table', methods=['POST'])
def search_table():
    data = request.json
    db_name = data.get('db_name')
    table_name = data.get('table_name')
    column = data.get('column')
    value = data.get('value')

    if not db_name or not table_name or not column or not value:
        return "Пожалуйста, укажите название базы данных, таблицу, столбец и значение для поиска.", 400

    try:
        db = f'{db_name}.db'
        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row  # This allows us to return rows as dictionaries
        cursor = conn.cursor()
        query = f"SELECT * FROM {table_name} WHERE {column} LIKE ?"
        cursor.execute(query, ('%' + value + '%',))
        rows = cursor.fetchall()
    except sqlite3.OperationalError as e:
        return str(e), 400
    finally:
        conn.close()

    if rows:
        results = [dict(row) for row in rows]
        return jsonify(results)
    else:
        return jsonify([])






# Фильтры
def query_db(db_name, query, args=(), one=False):
    conn = sqlite3.connect(f'{db_name}.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(query, args)
    rv = cur.fetchall()
    conn.close()
    return (rv[0] if rv else None) if one else rv

@app.route('/filter', methods=['POST'])
def filter_data():
    data = request.json
    db_name = data.get('db_name')
    table_name = data.get('table')
    filters = data.get('filters', [])

    if not db_name:
        return jsonify({"error": "Database name is required"}), 400
    if not table_name:
        return jsonify({"error": "Table name is required"}), 400

    query = f"SELECT * FROM {table_name} WHERE 1=1"
    params = []

    for f in filters:
        column = f.get('column')
        from_val = f.get('from')
        to_val = f.get('to')
        value = f.get('value')

        if column is None:
            continue

        if from_val is not None and from_val != "":
            query += f" AND {column} >= ?"
            params.append(from_val)
        if to_val is not None and to_val != "":
            query += f" AND {column} <= ?"
            params.append(to_val)
        if value is not None and value != "":
            if not column.isdigit():
                query += f" AND {column} LIKE ?"
                params.append(f"%{value}%")
            else:
                query += f" AND {column} = ?"
                params.append(value)

    results = query_db(db_name, query, params)
    return jsonify([dict(row) for row in results])




if __name__ == '__main__':
    app.run()