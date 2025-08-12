import telebot
from telebot import types
import requests
import platform
import fitz
from dotenv import load_dotenv
import os
import json
import re
import pytesseract
from PIL import Image
import io
import psycopg2
from psycopg2.extras import DictCursor

load_dotenv()

# === КОНФИГ ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
AI_API_KEY = os.getenv("AI_API_KEY")
AI_URL = "https://api.intelligence.io.solutions/api/v1/chat/completions"
MODEL = "deepseek-ai/DeepSeek-R1-0528"

tess_cmd = os.getenv('TESSERACT_CMD')

if tess_cmd and os.path.exists(tess_cmd):
    pytesseract.pytesseract.tesseract_cmd = tess_cmd
else:
    if platform.system() == "Windows":
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    else:
        pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract' #для Docker(LINUX)

print("Используемый путь Tesseract:", pytesseract.pytesseract.tesseract_cmd)


bot = telebot.TeleBot(TELEGRAM_TOKEN)

# === БАЗА ДАННЫХ ===
def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        dbname=os.getenv("DB_NAME"),
        cursor_factory=DictCursor
    )

def save_user_message(telegram_id, username, first_name, last_name, message_text):
    conn = get_db_connection()
    cur = conn.cursor()

    # Добавляем или обновляем пользователя
    cur.execute("""
        INSERT INTO users (telegram_id, username, first_name, last_name)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (telegram_id) DO UPDATE
        SET username = EXCLUDED.username,
            first_name = EXCLUDED.first_name,
            last_name = EXCLUDED.last_name
        RETURNING id
    """, (telegram_id, username, first_name, last_name))
    user_id = cur.fetchone()[0]

    # Добавляем сообщение пользователя
    cur.execute("""
        INSERT INTO user_messages (user_id, message_text)
        VALUES (%s, %s)
        RETURNING id
    """, (user_id, message_text))
    message_id = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    return message_id

def save_bot_response(user_message_id, response_text):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO bot_responses (user_message_id, response_text) VALUES (%s, %s)",
        (user_message_id, response_text)
    )
    conn.commit()
    cur.close()
    conn.close()

# === УТИЛИТЫ ===
def clean_response(text: str) -> str:
    text = re.sub(r"</?think>", "", text)
    text = re.sub(r"\([^)]*\)", "", text)
    return text.strip()

def chat_ai(prompt):
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Bearer {AI_API_KEY}"
    }
    data = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "Отвечай одним абзацем, без тегов <think> и повторов."},
            {"role": "user", "content": prompt}
        ]
    }
    try:
        payload = json.dumps(data, ensure_ascii=False).encode('utf-8')
        response = requests.post(AI_URL, headers=headers, data=payload)
        result = response.json()

        # Если нет choices, вернем весь ответ
        if "choices" in result and len(result["choices"]) > 0:
            return clean_response(result["choices"][0]["message"]["content"])
        else:
            return f"Ошибка LLM: {result}"
    except Exception as e:
        return f"Ошибка LLM: {e}"

def ocr_from_pdf(path):
    """Если в PDF нет текста, извлекаем через OCR"""
    doc = fitz.open(path)
    result_text = ""
    for page in doc:
        pix = page.get_pixmap(dpi=300)  # Рендер страницы в изображение
        img_bytes = pix.tobytes("png")  # Получаем PNG-байты
        img = Image.open(io.BytesIO(img_bytes))  # Преобразуем в PIL-изображение
        ocr_text = pytesseract.image_to_string(img, lang='rus+eng')  # Распознаем
        result_text += ocr_text + "\n"
    return result_text

def get_pdf_text(path):
    """Извлекает текст из PDF, если нет текста, использует OCR."""
    text = ""
    doc = fitz.open(path)
    for page in doc:
        text += page.get_text()

    if len(text.strip()) == 0: # Если текст пустой, используем OCR
        text = ocr_from_pdf(path)
    return text

def get_summary(text):
    """Краткое изложение текста."""
    return chat_ai(f"Сделай краткое изложение текста:\n{text[:4000]}")

# === ОБРАБОТЧИКИ ===
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Инфо", "Помощь")
    bot.send_message(
        message.chat.id,
        "Привет! Отправь PDF, и я сделаю краткое изложение.",
        reply_markup=markup
    )

@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(
        message.chat.id,
        "Доступные команды:\n"
        "/start - Приветствие и клавиатура\n"
        "/help - Список команд\n"
        "/info - Информация о пользователе\n"
        "Отправь PDF — я сделаю краткое изложение.\n"
        "Также можешь написать сообщение для общения с ИИ."
    )

@bot.message_handler(commands=['info'])
def info_command(message):
    bot.send_message(
        message.chat.id,
        f"Твой username: @{message.from_user.username}\n"
        f"ID: {message.from_user.id}"
    )

@bot.message_handler(content_types=['document'])
def handle_pdf(message):
    if not message.document.file_name.lower().endswith('.pdf'):
        bot.send_message(message.chat.id, "Отправь PDF файл.")
        return
    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    with open(message.document.file_name, "wb") as f:
        f.write(downloaded_file)
    try:
        bot.send_message(message.chat.id, "Обрабатываю PDF...")
        text = get_pdf_text(message.document.file_name)
        summary = get_summary(text)
        bot.send_message(message.chat.id, "Краткое изложение:\n" + summary)
    except Exception as e:
        bot.send_message(message.chat.id, "Ошибка: " + str(e))
    finally:
        os.remove(message.document.file_name)

@bot.message_handler(func=lambda message: message.text.lower() == "инфо")
def button_info(message):
    info_command(message)

@bot.message_handler(func=lambda message: message.text.lower() == "помощь")
def button_help(message):
    help_command(message)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        bot.send_message(message.chat.id, "Распознаю текст на изображении...")

        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        # Сохраняем временно
        filename = "temp_photo.png"
        with open(filename, 'wb') as f:
            f.write(downloaded_file)

        # OCR
        img = Image.open(filename)
        text = pytesseract.image_to_string(img, lang='rus+eng')

        if len(text.strip()) == 0:
            bot.send_message(message.chat.id, "Текст не распознан. Убедись, что изображение чёткое.")
        else:
            summary = get_summary(text)
            bot.send_message(message.chat.id, "Краткое изложение:\n" + summary)

    except Exception as e:
        bot.send_message(message.chat.id, "Ошибка при обработке изображения: " + str(e))
    finally:
        if os.path.exists("temp_photo.png"):
            os.remove("temp_photo.png")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    # Сохраняем сообщение пользователя
    user_message_id = save_user_message(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
        message_text=message.text
    )

    # Получаем ответ ИИ
    ai_reply = chat_ai(message.text)

    # Отправляем ответ пользователю
    bot.send_message(message.chat.id, ai_reply)

    # Сохраняем ответ бота
    save_bot_response(user_message_id, ai_reply)

if __name__ == "__main__":
    print("Бот запущен.")
    bot.polling(none_stop=True)