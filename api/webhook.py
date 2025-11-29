import telebot
import os
import requests
import logging
from flask import Flask, request # Используем Flask
from google import genai
from pydantic import BaseModel, Field, ValidationError

# --- 1. НАСТРОЙКА КЛЮЧЕЙ И МОДЕЛИ ---

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

if not TELEGRAM_TOKEN or not GOOGLE_API_KEY:
    logging.error("Ключи API не найдены.")
    exit()

client = genai.Client(api_key=GOOGLE_API_KEY)
bot = telebot.TeleBot(TELEGRAM_TOKEN)
MODEL_NAME = "gemini-2.5-flash"
# Создаем экземпляр Flask, который будет запущен Gunicorn
app = Flask(__name__) 

# --- 2. СИСТЕМНЫЙ ПРОМПТ (ХАРАКТЕР БОТА) ---

SYSTEM_PROMPT = """
Ты — Токсичный Комментатор, бот, который живет в Telegram-чате... (и т.д.)
"""
# ... (Остальной ваш SYSTEM_PROMPT остается прежним)

# --- 3. ФУНКЦИИ БОТА ---

def generate_toxic_response(text):
    # ... (Ваша функция generate_toxic_response остается без изменений) ...
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[
                {"role": "user", "parts": [{"text": text}]}
            ],
            config={
                "system_instruction": SYSTEM_PROMPT,
                "temperature": 0.9, 
                "max_output_tokens": 100
            }
        )
        return response.text
    except Exception as e:
        logging.error(f"Ошибка при запросе к Gemini API: {e}")
        return None

# Обработчик для ВСЕХ сообщений
@bot.message_handler(content_types=['text'])
def handle_all_messages(message):
    # ... (Ваша логика обработки сообщений остается прежней) ...
    # 10% вероятность ответа
    if requests.get('https://www.random.org/integers/?num=1&min=1&max=10&col=1&base=10&format=plain&rnd=new').text.strip() != '1':
        return

    logging.info(f"Сработал токсичный триггер на сообщение: {message.text[:50]}...")
    
    toxic_text = generate_toxic_response(message.text)

    if toxic_text:
        try:
            bot.reply_to(message, toxic_text)
        except Exception as e:
            logging.error(f"Ошибка при отправке сообщения в Telegram: {e}")

# --- 4. НАСТРОЙКА WEBHOOK ДЛЯ CLOUD RUN ---

# Этот эндпоинт принимает POST-запросы от Telegram
@app.route('/' + TELEGRAM_TOKEN, methods=['POST'])
def webhook():
    # Gunicorn запускает Flask, Flask обрабатывает запросы
    if request.method == 'POST':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'OK', 200
    return 'Hello, bot is waiting for Telegram messages.', 200

# Главный блок для установки Webhook (только если запускается локально)
if __name__ == '__main__':
    # Эта часть не используется Cloud Run/Gunicorn, но полезна для локального тестирования
    logging.info("Running locally - Polling or local Flask setup")
    
    # Чтобы установить Webhook вручную, используйте ваш URL Cloud Run:
    # bot.set_webhook(url="ВАШ_URL_CLOUD_RUN/" + TELEGRAM_TOKEN)
    
    # Для Gunicorn/Cloud Run нужен только экземпляр 'app'
    pass