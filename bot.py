import datetime

import telebot
import telegram
from sqlalchemy.orm import sessionmaker

from config import TOKEN
from crud import engine
from models import User, Message1
from telegramcalendar import create_calendar

# Base.metadata.create_all(engine)

current_shown_dates = {}

Session = sessionmaker(bind=engine)
s = Session()

bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    bot.reply_to(message, "Hi, zzzzver!")
    user = User(id=user_id, first_name=message.from_user.first_name, last_name=message.from_user.last_name)
    if user not in s.query(User).all():
        s.add(user)
        s.commit()


@bot.message_handler(commands=['calendar'])
def handle_calendar_command(message):

    now = datetime.datetime.now()
    chat_id = message.chat.id

    date = (now.year, now.month)
    current_shown_dates[chat_id] = date

    markup = create_calendar(now.year, now.month)

    bot.send_message(message.chat.id, "Please, choose a date", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: 'DAY' in call.data[0:13])
def handle_day_query(call):
    chat_id = call.message.chat.id
    saved_date = current_shown_dates.get(chat_id)
    last_sep = call.data.rfind(';') + 1

    if saved_date is not None:

        day = call.data[last_sep:]
        date = datetime.datetime(int(saved_date[0]), int(saved_date[1]), int(day), 0, 0, 0)
        bot.send_message(chat_id=chat_id, text=str(date))
        bot.answer_callback_query(call.id, text="")

    else:
        # add your reaction for shown an error
        pass


@bot.callback_query_handler(func=lambda call: 'MONTH' in call.data)
def handle_month_query(call):

    info = call.data.split(';')
    month_opt = info[0].split('-')[0]
    year, month = int(info[1]), int(info[2])
    chat_id = call.message.chat.id

    if month_opt == 'PREV':
        month -= 1

    elif month_opt == 'NEXT':
        month += 1

    if month < 1:
        month = 12
        year -= 1

    if month > 12:
        month = 1
        year += 1

    date = (year, month)
    current_shown_dates[chat_id] = date
    markup = create_calendar(year, month)
    bot.edit_message_text("Please, choose a date", call.from_user.id, call.message.message_id, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: "IGNORE" in call.data)
def ignore(call):
    bot.answer_callback_query(call.id, text="OOPS... something went wrong")


@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(message, bot.get_me())


@bot.message_handler(func=lambda message: True)
def upper(message: telebot.types.Message):
    bot.reply_to(message, message.text.upper())
    msg = Message1(update_id=message.message_id, text=message.text, sender_id=message.from_user.id)
    s.add(msg)
    s.commit()


bot.polling()

while True:
    pass
