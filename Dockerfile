FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем зависимости
RUN pip install --upgrade pip
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Копируем приложение в контейнер
COPY . /app
WORKDIR /app

# Открываем порт для Streamlit
EXPOSE 8501


# Запускаем приложение
CMD ["streamlit", "run", "main.py", "--server.port=8501"]