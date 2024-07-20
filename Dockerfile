FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y

COPY . .

RUN pip install --upgrade pip

RUN pip install -r requirements.txt

ENV T_BOT_ENDPOINT=
ENV BOT_TOKEN=

EXPOSE 8501

CMD ["streamlit", "run", "main.py"]
