# Telegram PDF/Photo AI Bot

Этот бот принимает PDF и изображения, извлекает из них текст, делает краткое изложение с помощью AI, а также умеет отвечать на обычные текстовые сообщения.  
Все входящие и исходящие сообщения сохраняются в PostgreSQL.

## Возможности
- 📄 Принимает PDF, извлекает текст или распознаёт через OCR (Tesseract)
- 🖼 Распознаёт текст с изображений (rus + eng)
- 🤖 Делает краткое изложение текста с помощью AI API
- 💬 Общается с пользователем в чате
- 💾 Сохраняет историю сообщений в PostgreSQL

## Установка

### 1. Клонирование репозитория
```bash
git clone https://github.com/username/project.git
cd project
```
### 2. Установка зависимостей
Убедись, что у тебя установлен Python 3.9+
```bash
Копировать код
pip install -r requirements.txt
```
### 3. Установка Tesseract OCR
Windows
Скачать и установить:
https://github.com/UB-Mannheim/tesseract/wiki

Linux (Debian/Ubuntu)
```bash
Копировать код
sudo apt update
sudo apt install tesseract-ocr
```
### 4. Настройка окружения
Скопируйте .env.example в .env:
```bash
cp .env.example .env
```
или через cmd
```bash
copy .env.example .env
```
Заполните .env своими токенами и паролями.

### 5. Запуск контейнеров
```bash
docker compose up -d --build
```
### 6. Применить миграции
Подождём, пока Postgres поднимется, и применим migrations/init.sql:
```bash
docker exec -it ai_telegram_bot-db-1 bash -lc 'until pg_isready -U user -d mybotdb; do sleep 1; done; psql -U user -d mybotdb -f /migrations/init.sql'
```
### 7. Проверка логов бота
```bash
docker logs -f telegram_bot
```

## Настройка базы данных
### 1. Установи PostgreSQL
### 2. Создай базу:
```bash
psql -U postgres -c "CREATE DATABASE bot_db;"
```
### 3. Выполни SQL-скрипты для создания таблиц:
```bash
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username TEXT,
    first_name TEXT,
    last_name TEXT
);

CREATE TABLE user_messages (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    message_text TEXT
);

CREATE TABLE bot_responses (
    id SERIAL PRIMARY KEY,
    user_message_id INT REFERENCES user_messages(id) ON DELETE CASCADE,
    response_text TEXT
);
```
## Запуск
```bash
python bot.py
```

Если хочешь запустить в Docker:
```bash
docker build -t pdf-ai-bot .
docker run --env-file .env pdf-ai-bot
```
## Использование
/start — приветствие и кнопки

/help — список команд

/info — информация о пользователе

Отправь PDF — бот сделает краткое изложение

Отправь фото с текстом — бот распознает текст и сделает краткое изложение

Напиши сообщение — бот ответит, как чат-бот

## Стек технологий
Python 3

pyTelegramBotAPI

PostgreSQL

PyMuPDF (fitz)

Tesseract OCR

Requests (для AI API)

# Структура проекта

bot/ — код Telegram-бота

migrations/ — SQL-скрипты для создания таблиц

docker-compose.yml — описание сервисов для запуска в Docker

Dockerfile — сборка образа бота

.env.example — пример конфигурации окружения

# Структура базы данных

users — данные пользователей

user_messages — сообщения пользователей

bot_responses — ответы бота

# Важно

Никогда не коммитьте свой реальный .env и свои данные в репозиторий.

## Лицензия
MIT License — используй свободно, но указывай автора.