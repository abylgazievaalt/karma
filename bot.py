import psycopg2
import telebot
import schedule
import logging

from sqlalchemy.orm import sessionmaker
from telebot import types

from config import TOKEN
from crud import engine, recreate_database, Base
from models import User, Message1

Base.metadata.create_all(engine)
recreate_database()

Session = sessionmaker(bind=engine)
s = Session()

logger = telebot.logger
telebot.logger.setLevel(logging.INFO)

bot = telebot.TeleBot(TOKEN)
#app = flask.Flask(__name__)


import datetime
from datetime import timedelta
import time

# busy_from = datetime.datetime(2019, 12, 10)
# busy_to = datetime.datetime(2019, 12, 16)
# now = datetime.datetime.today().weekday()
# now_day = datetime.datetime.today()
# a = (now_day - busy_to)
# delta1 = timedelta(days=5)
# print(a)
# print(now)

def increment_busyness():
    for user in s.query(User):
        date_from = user.busy_from_date
        date_to = user.busy_to_date
        now = datetime.date.today()
        if now >= date_from and now <= date_to:
            user.busyness_points += 4


@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    user = s.query(User).get(message.from_user.id)
    if user not in s.query(User).all():
        bot.reply_to(message, "Hi, new zzzzver!")
        new_user = User(id=user_id, first_name=message.from_user.first_name, last_name=message.from_user.last_name)
        s.add(new_user)
        s.commit()

    else:
        bot.reply_to(message, "Hi, old zzzzver!")

schedule.every().saturday.at("14:03").do(increment_busyness)

@bot.message_handler(commands=['busyfromto'])
def busy_from(message):
    markup = types.ForceReply(selective=False)
    reply_msg = bot.send_message(chat_id=message.chat.id, text="Enter start date, in such format: 01/01/2019",
                                 reply_markup=markup)
    bot.register_next_step_handler(reply_msg, save_date_from)


def save_date_from(message):
    date = message.text
    list = date.split('/', maxsplit=2)
    busy_from = datetime.datetime(int(list[2]), int(list[1]), int(list[0]))
    year = list[2]
    month = list[1]
    day = list[0]
    isValidDate = True
    try:
        datetime.datetime(int(year), int(month), int(day))
    except ValueError:
        isValidDate = False
    if (not isValidDate):
        bot.send_message(message.chat.id, "Input date is not valid. Try again.")

    user_id = message.from_user.id
    user = s.query(User).get(user_id)
    user.busy_from_date = busy_from
    s.add(user)
    s.commit()
    markup = types.ForceReply(selective=False)
    reply_msg = bot.send_message(chat_id=message.chat.id, text="Enter deadline date, in such format: 01/01/2019",
                                 reply_markup=markup)
    bot.register_next_step_handler(reply_msg, save_date_to)


def save_date_to(message):
    bot.send_message(message.chat.id, "Your project dates are saved!")
    date = message.text
    list = date.split('/', maxsplit=2)
    busy_to = datetime.datetime(int(list[2]), int(list[1]), int(list[0]))
    year = list[2]
    month = list[1]
    day = list[0]
    isValidDate = True
    try:
        datetime.datetime(int(year), int(month), int(day))
    except IndexError:
        isValidDate = False
    if (not isValidDate):
        bot.send_message(message.chat.id, "Input date is not valid. Try again.")
    user_id = message.from_user.id
    user = s.query(User).get(user_id)
    user.busy_to_date = busy_to
    s.add(user)
    s.commit()


@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(message, bot.get_me())


@bot.message_handler(commands=['getactivity'])
def get_users(message):
    connection = psycopg2.connect(user="postgres", password="Anbanb201299", host="localhost",
                                  port="5432", database="finalBotDb")
    cursor = connection.cursor()
    mes_id = message.from_user.id
    cursor.execute("select count(*) from message where sender_id = '%s'", [mes_id])
    records = cursor.fetchall()

    high = 2
    normal = 1
    low = 0

    user = s.query(User).get(message.from_user.id)

    if records[0][0] > 15:
        bot.reply_to(message, ('Activity: normal, activity points = {}, messages = %d' % records[0][0]).format(normal))
        user.activity_points = 2
    elif records[0][0] > 30:
        bot.reply_to(message, ('Activity: high, activity points = {}, messages = %d' % records[0][0]).format(high))
        user.activity_points = 4
    else:
        bot.reply_to(message, ('Activity: low, activity points = {}, messages = %d' % records[0][0]).format(low))


@bot.message_handler(commands=['getbusyness'])
def get_users(message):
    user_id = message.from_user.id
    user = s.query(User).get(user_id)
    bot.reply_to(message, user.busyness_points)


@bot.message_handler(commands=['getpoints'])
def get_points(message):
    user_id = message.from_user.id
    user = s.query(User).get(user_id)
    total_points = user.busyness_points + user.activity_points + user.mentorship_points + user.reports_points
    if total_points > 10:
        total_points = 10
    bot.send_message(chat_id=message.chat.id, text=total_points)


@bot.message_handler(commands=['getmentorship'])
def get_mentorship_points(message):
    user_id = message.from_user.id
    user = s.query(User).get(user_id)
    bot.send_message(chat_id=message.chat.id, text=user.mentorship_points)


@bot.message_handler(commands=['mentee'])
def get_mentee_report(message):
    chat_id_mentor = message.chat.id
    # Форсим реплай
    markup = types.ForceReply(selective=False)
    reply = bot.send_message(chat_id=chat_id_mentor, text="Write a weekly report about your mentee.",
                            reply_markup=markup)
    bot.register_next_step_handler(reply, forward_msg)

# forward message to teamlead and require a feedback
def forward_msg(message):
    if message:
        # msg from mentor
        forward_msg.forward_from = message.chat.id  # mentor - bot chat
        if forward_msg.forward_from:
            forward_msg.mentor = s.query(User).get(message.from_user.id)
            forward_msg.name = forward_msg.mentor.first_name
            forward_to = 512225760 # teamlead - bot chat
            # msg is sent to teamlead
            bot.forward_message(forward_to, forward_msg.forward_from, message.message_id)
            bot.send_message(chat_id=message.chat.id, text="Your message was sent to teamlead.")
            markup = types.ForceReply(selective=False)
            #require teamlead to write a feedback to mentor
            reply = bot.send_message(chat_id=forward_to,
                                     text="Give {0} a feedback.".format(forward_msg.name),
                                     reply_markup=markup)

            bot.register_next_step_handler(reply, forward_msg2)

# force teamlead to rate mentor
def forward_msg2(message):
    forward_from = message.chat.id  # teamlead - bot chat
    forward_to = forward_msg.forward_from
    if message:
        bot.forward_message(forward_to, forward_from, message.message_id)
        bot.send_message(chat_id=forward_from, text="Your message was sent to {0}".format(forward_msg.name))

    markup = types.ForceReply(selective=False)
    reply = bot.send_message(chat_id=message.chat.id,
                             text="Rate {0}'s communication with mentee.".format(forward_msg.name),
                             reply_markup=markup)
    bot.register_next_step_handler(reply, parse_points)

def parse_points(message):
    try:
        points = int(message.text)
        mentor = forward_msg.mentor
        if points > 4:
            points = 4
        mentor.mentorship_points = points
        bot.send_message(chat_id=message.chat.id, text="Rate points were saved in database.")
        bot.send_message(chat_id=forward_msg.forward_from, text="Your mentorship points = {0}.".format(points))
    except ValueError:
        bot.send_message(chat_id=message.chat.id, text="It must be a number!")
        markup = types.ForceReply(selective=False)
        reply = bot.send_message(chat_id=message.chat.id,
                                 text="Rate {0}'s communication with mentee in range 0-4.".format(forward_msg.name),
                                 reply_markup=markup)
        bot.register_next_step_handler(reply, parse_points)


@bot.message_handler(func=lambda message: True)
def upper(message: telebot.types.Message):
    msg = Message1(update_id=message.message_id, text=message.text, sender_id=message.from_user.id,
                   chat_id=message.chat.id)
    s.add(msg)
    s.commit()


# @app.route("/{}".format(TOKEN), methods=['POST'])
# def getMessage():
#     bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
#     return "!", 200


if __name__ == '__main__':
    bot.remove_webhook()
    time.sleep(0.1)
    bot.polling()


