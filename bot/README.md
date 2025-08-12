# Telegram AI Bot

Бот для Telegram, который принимает PDF и фото, распознаёт текст (OCR), делает краткое изложение с помощью AI.

## Установка и запуск

### 1. Склонируйте репозиторий

```bash
git clone https://github.com/Alik05-WW/AI_telegram_bot.git
cd ai_telegram_bot
```
### 2. Создайте файл `.env`

Скопируйте `.env.example` в `.env` и заполните своими токенами и паролями:

```bash
cp .env.example .env
```
Откройте файл .env и заполните его своими данными, примерно так:

```env
# Токен Telegram-бота (получить у @BotFather)
TELEGRAM_TOKEN=ВАШ_ТОКЕН_ТЕЛЕГРАМ_БОТА

# Ключ API для AI-сервиса
AI_API_KEY=ВАШ_API_КЛЮЧ_ИИ

# Параметры подключения к базе данных PostgreSQL
DB_HOST=db
DB_PORT=5432
DB_USER=user
DB_PASSWORD=password
DB_NAME=mybotdb

TESSERACT_CMD=/usr/bin/tesseract
# Для Windows пример:
# TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
```
### 3.  Запустите проект
```bash
docker-compose up --build -d
```
### 4. Выполните миграцию базы данных
Зайдите в контейнер базы:
```bash
docker exec -it ai_telegram_bot-db-1 psql -U user -d mybotdb
```
Выполните SQL-скрипт миграции:

```sql
\i /migrations/init.sql
```
## Лицензия

MIT