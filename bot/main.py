import telebot
from telebot import types
import requests
import fitz
from dotenv import load_dotenv
import os
import json
import re
import pytesseract
from PIL import Image
import io
import psycopg2

load_dotenv()

# === КОНФИГ ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
AI_API_KEY = os.getenv("AI_API_KEY")
AI_URL = "https://api.intelligence.io.solutions/api/v1/chat/completions"
MODEL = "deepseek-ai/DeepSeek-R1-0528"

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# === БАЗА ДАННЫХ ===
def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        dbname=os.getenv("DB_NAME")
    )

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
def chat_with_ai(message):
    bot.send_message(message.chat.id, chat_ai(message.text))

@bot.message_handler(func=lambda message: True)
def chat_with_ai(message):
    save_user_message(message.from_user.id, message.text)
    bot.send_message(message.chat.id, chat_ai(message.text))

if __name__ == "__main__":
    print("Бот запущен.")
    bot.polling(none_stop=True)