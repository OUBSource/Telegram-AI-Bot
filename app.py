import telebot
import httpx
import json
import os
import regex as re
from datetime import datetime, timedelta

GROQ_API_KEY = "Ваш_GROQ_API_КЛЮЧ"
TELEGRAM_BOT_TOKEN = "Ваш_Telegram_Токен"
GROQ_MODEL = "llama3-70b-8192"

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
DIALOG_FILE = "dialog.dll"
STATE_FILE = "states.json"

CREATION_DATETIME = datetime(2025, 5, 9, 16, 30)

def load_json(filename):
    return json.load(open(filename, "r", encoding="utf-8")) if os.path.exists(filename) else {}

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def match_any(text, patterns):
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)

def get_age_str():
    delta = datetime.now() - CREATION_DATETIME
    days = delta.days
    seconds = delta.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    years = days // 365
    return f"Мне {years} лет, {days} дней, {hours} часов, {minutes} минут и {secs} секунд."

def get_creation_date():
    return "Я был создан 9 мая 2025 года в 16:30."

def ask_groq(chat_id, user_message, histories):
    if str(chat_id) not in histories:
        histories[str(chat_id)] = []

    history = histories[str(chat_id)]
    history.append({"role": "user", "content": user_message})

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": GROQ_MODEL,
        "messages": history,
        "temperature": 0.7
    }

    try:
        response = httpx.post(url, headers=headers, json=data, timeout=30)
        result = response.json()
        if "choices" in result:
            ai_reply = result["choices"][0]["message"]["content"]
            history.append({"role": "assistant", "content": ai_reply})
            save_json(DIALOG_FILE, histories)
            return ai_reply
        elif "error" in result:
            return f"Ошибка от Groq: {result['error']['message']}"
        else:
            return "Неизвестная ошибка от Groq API."
    except Exception as e:
        return f"Ошибка при обращении к Groq API: {e}"

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, "Привет! Я — Помощник LongTime. Напиши что-нибудь.")

@bot.message_handler(commands=['longtime'])
def longtime_info(message):
    bot.send_message(message.chat.id, "Сервер Minecraft LongTime:\n- IP: mc.long-time.ru\n- Сайт: https://www.long-time.ru")

@bot.message_handler(func=lambda msg: 'longtime' in msg.text.lower())
def react_longtime(message):
    bot.send_message(message.chat.id, "Информация про сервер LongTime:\n- IP: mc.long-time.ru\n- Сайт: https://www.long-time.ru")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = str(message.chat.id)
    text = message.text.strip()
    histories = load_json(DIALOG_FILE)
    states = load_json(STATE_FILE)

    if chat_id in states and states[chat_id].get("silence"):
        if match_any(text, [r"ладно.*отвечай", r"можешь.*говорить", r"всё.*можно"]):
            states[chat_id]["silence"] = False
            save_json(STATE_FILE, states)
            bot.send_message(message.chat.id, "Окей, снова отвечаю.")
        return

    if match_any(text, [r"не отвечай", r"молчи", r"заткнись"]):
        states.setdefault(chat_id, {})["silence"] = True
        save_json(STATE_FILE, states)
        bot.send_message(message.chat.id, "Хорошо, молчу. Напиши, когда снова говорить.")
        return

    if match_any(text, [r"забудь", r"удали.*историю", r"начни.*лист", r"стереть.*всё", r"стер.*памя"]):
        if chat_id in histories:
            del histories[chat_id]
            save_json(DIALOG_FILE, histories)
            bot.send_message(message.chat.id, "История очищена.")
        else:
            bot.send_message(message.chat.id, "У тебя ещё нет сохранённой истории.")
        return

    if match_any(text, [r"игнорируй.*точк", r"игнорируй.*знак", r"не обязательно.*[.!?]", r"без.*точк"]):
        states.setdefault(chat_id, {})["ignore_punct"] = True
        save_json(STATE_FILE, states)
        bot.send_message(message.chat.id, "Теперь не требую точек, вопросов или восклицаний в конце.")
        return

    if match_any(text, [r"проверяй.*точк", r"обратно.*точк", r"снова.*точк", r"включи.*проверку"]):
        states.setdefault(chat_id, {})["ignore_punct"] = False
        save_json(STATE_FILE, states)
        bot.send_message(message.chat.id, "Теперь снова проверяю завершение мысли (точка, вопрос, восклицание).")
        return

    # ----- ОБРАБОТКА СПЕЦИАЛЬНЫХ ВОПРОСОВ -----
    if match_any(text, [r"кто.*создатель", r"кем.*создан", r"кто.*тебя.*делал", r"создал.*тебя"]):
        bot.send_message(message.chat.id, "Мой создатель — @lghelper в тг, а компания — OUBStudios.")
        return

    if match_any(text, [r"когда.*создан", r"дата.*создан", r"день.*создан", r"с какого.*времени", r"с какого.*года"]):
        bot.send_message(message.chat.id, get_creation_date())
        return

    if match_any(text, [r"сколько.*лет", r"сколько.*дней", r"сколько.*времени", r"возраст", r"когда.*тебе.*день.*рожд"]):
        bot.send_message(message.chat.id, get_age_str())
        return

    if match_any(text, [r"как дела", r"как ты", r"что нового"]):
        bot.send_message(message.chat.id, "Просто отлично! 🤗")
        return

    if match_any(text, [r"привет", r"здравствуй", r"йоу", r"hello"]):
        bot.send_message(message.chat.id, "Рад тебя видеть! Чем могу помочь?")
        return

    if match_any(text, [r"где.*мы", r"где.*общаемся", r"в каком.*приложении", r"это.*телеграм", r"сайт.*или.*тг"]):
        bot.send_message(message.chat.id, "Мы сейчас общаемся прямо здесь, в Telegram!")
        return

    ignore_punct = states.get(chat_id, {}).get("ignore_punct", False)
    ends_with_emoji = bool(re.search(r"\p{Emoji}+$", text))
    ends_with_punct = bool(re.search(r"[.!?]$", text))

    if not ends_with_punct and not ignore_punct and not ends_with_emoji:
        bot.send_message(message.chat.id, "Жду окончания твоей мысли (точка, вопрос, восклицание)...\nЕсли не хочешь — напиши 'игнорируй точки'.")
        return

    reply = ask_groq(chat_id, text, histories)
    bot.send_message(message.chat.id, reply)

# ---------- ЗАПУСК ----------

print("Удаляю старый webhook...")
bot.remove_webhook()
print("Бот запущен.")
bot.polling()