import telebot
from dotenv import load_dotenv
import os
import time
import datetime


load_dotenv("api_master.env")
load_dotenv("id_list.env")
TOKEN = os.getenv("TOKEN")
admin_id = os.getenv("admin_id")

bot = telebot.TeleBot(TOKEN)

# Часовий пояс
UTC_OFFSET = 3  # UTC+3

# Стан зміни
admin_start_time = None
admin_on_break = False
admin_keyboard_sent = False
admin_shift_date = None
admin_shift_closed = False

pause_start_time = None
total_pause_time = 0

# Ролі юзерів
user_roles = {}  # user_id: "admin" або "user"


def local_now():
    """Повертає поточний час з урахуванням UTC+3"""
    return datetime.datetime.utcnow() + datetime.timedelta(hours=UTC_OFFSET)

def get_shift_date(now=None):
    """Робоча дата (новий день починається о 10:00)"""
    if now is None:
        now = local_now()
    if now.hour < 10:
        return (now - datetime.timedelta(days=1)).date()
    return now.date()

def admin_panel(chat_id, on_break=False, notify=False):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = telebot.types.KeyboardButton("▶ ON")
    if on_break:
        item2 = telebot.types.KeyboardButton("▶ CONTINUE")
    else:
        item2 = telebot.types.KeyboardButton("⏸ Break")
    item3 = telebot.types.KeyboardButton("⏹ OFF")
    markup.add(item1, item2, item3)
    if notify:
        bot.send_message(chat_id, "Оберіть дію:", reply_markup=markup)
    else:
        bot.send_message(chat_id, ".", reply_markup=markup)

def default_panel(chat_id, notify=False):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = telebot.types.KeyboardButton("🧐")
    markup.add(item1)
    if notify:
        bot.send_message(chat_id, "Ваша роль: користувач", reply_markup=markup)
    else:
        bot.send_message(chat_id, ".", reply_markup=markup)


@bot.message_handler(content_types=['text'])
def handle_text(message):
    global admin_start_time, admin_on_break, admin_keyboard_sent
    global admin_shift_date, admin_shift_closed, pause_start_time, total_pause_time, user_roles

    user_id = message.from_user.id
    today = get_shift_date()

    # Визначення ролі
    if user_id not in user_roles:
        if str(user_id) == str(admin_id):
            user_roles[user_id] = "admin"
            admin_panel(message.chat.id, admin_on_break, notify=True)
            admin_keyboard_sent = True
        else:
            user_roles[user_id] = "user"
            default_panel(message.chat.id, notify=True)

    # Логіка адміна
    if str(user_id) == str(admin_id):
        if message.text == "/admin":
            admin_panel(message.chat.id, admin_on_break, notify=True)
            admin_keyboard_sent = True

        elif message.text == "▶ ON":
            if admin_start_time and not admin_shift_closed and admin_shift_date == today:
                bot.send_message(message.chat.id, "Зміна вже активна!")
            else:
                admin_start_time = time.time()
                admin_on_break = False
                admin_shift_date = today
                admin_shift_closed = False
                pause_start_time = None
                total_pause_time = 0
                start_dt = local_now()
                formatted_start = start_dt.strftime("%H:%M:%S")
                bot.send_message(message.chat.id, f"Зміна почата в: {formatted_start}")
                if not admin_keyboard_sent:
                    admin_panel(message.chat.id, admin_on_break, notify=True)
                    admin_keyboard_sent = True

        elif message.text == "⏸ Break":
            if admin_start_time and not admin_on_break and not admin_shift_closed:
                pause_start_time = time.time()
                admin_on_break = True
                session_time = pause_start_time - admin_start_time - total_pause_time
                formatted_time = str(datetime.timedelta(seconds=int(session_time)))
                markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
                markup.add(
                    telebot.types.KeyboardButton("▶ ON"),
                    telebot.types.KeyboardButton("▶ CONTINUE"),
                    telebot.types.KeyboardButton("⏹ OFF"),
                )
                bot.send_message(message.chat.id, f"Перерва розпочата! Відпрацьовано до паузи: {formatted_time}", reply_markup=markup)
            else:
                bot.send_message(message.chat.id, "Зміна ще не почата, вже на перерві або закрита!")

        elif message.text == "▶ CONTINUE":
            if admin_on_break and not admin_shift_closed and pause_start_time:
                total_pause_time += time.time() - pause_start_time
                pause_start_time = None
                admin_on_break = False
                markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
                markup.add(
                    telebot.types.KeyboardButton("▶ ON"),
                    telebot.types.KeyboardButton("⏸ Break"),
                    telebot.types.KeyboardButton("⏹ OFF"),
                )
                bot.send_message(message.chat.id, "Зміна продовжена!", reply_markup=markup)
            else:
                bot.send_message(message.chat.id, "Ви не на перерві або зміна закрита!")

        elif message.text == "⏹ OFF":
            if admin_start_time and not admin_shift_closed and admin_shift_date == today:
                if admin_on_break and pause_start_time:
                    total_pause_time += time.time() - pause_start_time
                    pause_start_time = None
                    admin_on_break = False
                admin_shift_closed = True
                bot.send_message(message.chat.id, f"Зміна закрита! ({today.strftime('%d.%m.%Y')})")
            else:
                bot.send_message(message.chat.id, "Зміна не активна або вже закрита!")

        elif message.text == "🧐":
            if admin_shift_closed and admin_shift_date == today:
                bot.send_message(message.chat.id, f"Зміна на {today.strftime('%d.%m.%Y')} вже закрита!")
            elif admin_start_time and not admin_shift_closed and admin_shift_date == today:
                if admin_on_break and pause_start_time:
                    pause_duration = time.time() - pause_start_time
                    formatted_pause = str(datetime.timedelta(seconds=int(pause_duration)))
                    bot.send_message(message.chat.id, f"Перерва триває: {formatted_pause}")
                else:
                    session_time = time.time() - admin_start_time - total_pause_time
                    formatted_time = str(datetime.timedelta(seconds=int(session_time)))
                    bot.send_message(message.chat.id, f"Зміна триває: {formatted_time}")
            else:
                bot.send_message(message.chat.id, "Зміна ще не почата!")

    # Логіка користувачів
    else:
        if message.text == "🧐":
            if admin_start_time and not admin_shift_closed and admin_shift_date == today:
                if admin_on_break and pause_start_time:
                    pause_duration = time.time() - pause_start_time
                    formatted_pause = str(datetime.timedelta(seconds=int(pause_duration)))
                    bot.send_message(message.chat.id, f"Перерва триває: {formatted_pause}")
                else:
                    session_time = time.time() - admin_start_time - total_pause_time
                    formatted_time = str(datetime.timedelta(seconds=int(session_time)))
                    total_shift_seconds = 6 * 60 * 60
                    remaining_seconds = max(0, total_shift_seconds - session_time)
                    formatted_remaining = str(datetime.timedelta(seconds=int(remaining_seconds)))
                    bot.send_message(
                        message.chat.id,
                        f"Відпрацьовано: {formatted_time}\nЗалишилось до кінця зміни: {formatted_remaining}"
                    )
            elif admin_shift_closed and admin_shift_date == today:
                bot.send_message(message.chat.id, f"Зміна на {today.strftime('%d.%m.%Y')} вже закрита!")
            else:
                bot.send_message(message.chat.id, "Зміна ще не почата!")

def run_bot():
    while True:
        try:
            print("Бот запускається...")
            bot.polling(none_stop=True, timeout=60, long_polling_timeout=30)
        except Exception as e:
            print(f"[ERROR] Бот впав: {e}")
            time.sleep(15)
            continue

if __name__ == "__main__":
    run_bot()
