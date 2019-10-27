from sqlalchemy.orm import sessionmaker

from crud import engine, recreate_database
from models import Base, User, Message1
from config import TOKEN

import telebot
#from telebot.types import Message

recreate_database()

Session = sessionmaker(bind=engine)
s = Session()

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    bot.reply_to(message, "Hi, zzzzver!")
    user = User(id=user_id, first_name=message.from_user.first_name, last_name=message.from_user.last_name)
    s.add(user)
    s.commit()

@bot.message_handler(commands=['help', 'busyfromto'])
def send_help(message):
    bot.reply_to(message, bot.get_me())


@bot.message_handler(func=lambda message: True)
def upper(message: telebot.types.Message):
    bot.reply_to(message, message.text.upper())
    #user = s.query(User).one()
    msg = Message1(update_id=message.message_id, text=message.text, sender_id=message.from_user.id)
    s.add(msg)
    s.commit()


bot.polling()

while True:
    pass
