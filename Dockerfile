# Используем базовый образ Python
FROM python:3.9

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Устанавливаем зависимости
RUN pip install \
    Flask \
    Flask-SQLAlchemy \
    Flask-Cors \
    pandas \ 
    openpyxl \
    temp

# Копируем исходный код приложения в контейнер
COPY . .

# Устанавливаем переменную окружения для Flask
ENV FLASK_APP=main.py

# Запускаем приложение Flask
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
EXPOSE 5000

