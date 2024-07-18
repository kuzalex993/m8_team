FROM python:3.10-slim
EXPOSE 8080
WORKDIR /app
RUN apt-get update && apt-get install -y
RUN pip install --upgrade pip
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . /app

# Запускаем приложение
ENTRYPOINT ["streamlit", "run", "main.py", "--server.port=8080", "--server.address=0.0.0.0"]