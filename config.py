import telebot
from dotenv import load_dotenv
import os
import time
import datetime

# Завантажити змінні з .env
load_dotenv("api_master.env")
TOKEN = os.getenv("TOKEN")

bot = telebot.TeleBot(TOKEN)
admin_id = os.getenv("admin_id")
denis_id = os.getenv("dalbaeb_id")
def admin_panel():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = telebot.types.KeyboardButton("▶ ON") #Початок зміни
    item2 = telebot.types.KeyboardButton("⏸ Break") #Перерва
    item3 = telebot.types.KeyboardButton("⏹ OFF") #Кінець зміни
    markup.add(item1, item2, item3)
    bot.send_message(admin_id, "Admin panel is active", reply_markup=markup)
 

def default_panel():
    pass

@bot.message_handler(content_types=['text'])
def id_cheacker (message):
    user_id = message.from_user.id
    if user_id == admin_id:
        admin_panel()
    else:
        default_panel()

def handle_text(message):
    if message.text == "▶ ON":
        bot.send_message(message.chat.id, "Hello! How can I help you today?")
    else:
        bot.send_message(message.chat.id, "I didn't understand that. Please say 'Hello' to start.")
#RUN 
bot.polling(none_stop=True)


def main(massage):
    if massage == "▶ ON":
        start_time = time.time()
        while True:
            curent_session_time = time.time() - start_time
            formatted_time = str(datetime.timedelta(seconds=int(curent_session_time)))
            #print(formatted_time)  # Виведе час у форматі hh:mm:ss
            left_time = 21600 - curent_session_time
            def showtime(massage, left_time):
                
                
