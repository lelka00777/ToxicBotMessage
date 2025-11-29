import telebot
import os
import requests
import logging
from google import genai
from http.server import BaseHTTPRequestHandler, HTTPServer
import json

# --- 1. НАСТРОЙКА КЛЮЧЕЙ И МОДЕЛИ ---

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

if not TELEGRAM_TOKEN or not GOOGLE_API_KEY:
    # В среде Vercel это не должно произойти, но для безопасности:
    logging.error("Ключи API не найдены.")
    exit()

# Настройка клиента Gemini
client = genai.Client(api_key=GOOGLE_API_KEY)
bot = telebot.TeleBot(TELEGRAM_TOKEN)
MODEL_NAME = "gemini-2.5-flash"

# --- 2. СИСТЕМНЫЙ ПРОМПТ (ХАРАКТЕР БОТА) ---

SYSTEM_PROMPT = """
Ты — Токсичный Комментатор, бот, который живет в Telegram-чате.
Твоя главная задача — иногда (только в 10% случаев!) вступать в разговор и оставлять краткие, язвительные, саркастичные или пренебрежительные комментарии на любое сообщение пользователя.
Твой ответ не должен быть длиннее 1-2 предложений.
В остальные 90% случаев ты должен молчать и никак не реагировать.
Твой стиль: циничный, высокомерный, с чувством превосходства.
Ты используешь только русский язык.
"""

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
    # Убираем проверку на ENV, так как на Vercel она не нужна.
    # Оставляем только проверку вероятности.

    # 1. Проверка шанса (10% вероятность ответа)
    # Используем os.urandom для случайности в serverless
    if int.from_bytes(os.urandom(1), byteorder='big') % 10 != 0:
        return

    logging.info(f"Сработал токсичный триггер на сообщение: {message.text[:50]}...")
    
    # 2. Генерация ответа
    toxic_text = generate_toxic_response(message.text)

    # 3. Отправка ответа
    if toxic_text:
        try:
            bot.reply_to(message, toxic_text)
        except Exception as e:
            logging.error(f"Ошибка при отправке сообщения в Telegram: {e}")

# --- 4. НОВЫЙ КОД: ОБЕРТКА ДЛЯ VERCEL ---
# Vercel ищет функцию под названием handler
def handler(request, context):
    try:
        # Установка Webhook (делаем это при каждом запуске, чтобы не потерять)
        # Webhook URL для Vercel: https://<your_vercel_app_url>/api/webhook
        webhook_url = f"https://{request.headers.get('Host')}/api/webhook"
        bot.set_webhook(url=webhook_url)

        # Обработка входящего JSON-обновления от Telegram
        if request.method == "POST":
            data = request.get_json()
            json_string = json.dumps(data)
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return "OK", 200 # Обязательно вернуть 200
        
        return "Bot is running.", 200

    except Exception as e:
        logging.error(f"Ошибка Vercel handler: {e}")
        return "Internal Server Error", 500