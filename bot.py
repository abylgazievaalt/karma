import datetime
import os
import time

import psycopg2
import telebot
import schedule
import logging
import flask
from flask import Flask, request

from sqlalchemy.orm import sessionmaker
from telebot import types
from config import TOKEN
from crud import engine, recreate_database
from models import User, Message1

# Base.metadata.create_all(engine)
# recreate_database()


# WEBHOOK_HOST = 'https://api.telegram.org/bot%s/getWebhookInfo' % (TOKEN)
# WEBHOOK_PORT = 8443  # 443, 80, 88 or 8443 (port need to be 'open')
# WEBHOOK_LISTEN = '0.0.0.0'  # In some VPS you may need to put here the IP address


# WEBHOOK_SSL_CERT = './webhook_cert.pem'  # Path to the ssl certificate
# WEBHOOK_SSL_PRIV = './webhook_pkey.pem'  # Path to the ssl private key
# WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
# WEBHOOK_URL_PATH = "/%s/" % (TOKEN)


Session = sessionmaker(bind=engine)
s = Session()

logger = telebot.logger
telebot.logger.setLevel(logging.INFO)

bot = telebot.TeleBot(TOKEN)
app = flask.Flask(__name__)

@app.route('/', methods=['GET', 'HEAD'])
def index():
    return ''


# @app.route(WEBHOOK_URL_PATH, methods=['POST'])
# def webhook():
#     if flask.request.headers.get('content-type') == 'application/json':
#         json_string = flask.request.get_data().decode('utf-8')
#         update = telebot.types.Update.de_json(json_string)
#         bot.process_new_updates([update])
#         return ''
#     else:
#         flask.abort(403)


def increment_busyness():
    for user in s.query(User):
        date_from = user.busy_from_date
        date_to = user.busy_to_date
        now = datetime.date.today()
        if now >= date_from and now <= date_to:
            user.busyness_points += 4


#schedule.every(3).seconds.do(increment_busyness)


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


schedule.every().sunday.at("12:35").do(increment_busyness)

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
    #connection = psycopg2.connect(user="postgres", password="Anbanb201299", host="localhost",
    #                              port="5432", database="finalBotDb")
    #cursor = connection.cursor()

    #cursor.execute("select busyness_points+activity_points+ from user where id = '%s'", [user_id])
    #records = cursor.fetchall()

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
        mentor.mentorship_points = points
        bot.send_message(chat_id=message.chat.id, text="Rate points were saved in database.")
        bot.send_message(chat_id=forward_msg.forward_from, text="Your mentorship points = {0}.".format(points))
    except ValueError:
        bot.send_message(chat_id=message.chat.id, text="It must be a number!")
        markup = types.ForceReply(selective=False)
        reply = bot.send_message(chat_id=message.chat.id,
                                 text="Rate {0}'s communication with mentee.".format(forward_msg.name),
                                 reply_markup=markup)
        bot.register_next_step_handler(reply, parse_points)

    #     if forward_from:
    #         text = 'Сообщение от тимлида:\n\n' + message.text
    #         bot.send_message(
    #             chat_id=forward_from.id,
    #             text=text,
    #         )
    #         reply = 'Сообщение было отправлено'
    #     else:
    #         error_message = 'Нельзя ответить самому себе'
    # else:
    #     error_message = 'Сделайте reply чтобы ответить автору сообщения'
    #
    # # Отправить сообщение об ошибке если оно есть
    # # if error_message is not None:
    # #     reply = error_message
    # # else:
    #     # Пересылать всё как есть
    #     bot.forward_message(message.chat.id, 512225760)
    #     bot.send_message(message.from_user.id,
    #         text='Сообщение было отправлено',
    #     )

@bot.message_handler(func=lambda message: True)
def upper(message: telebot.types.Message):
    msg = Message1(update_id=message.message_id, text=message.text, sender_id=message.from_user.id,
                   chat_id=message.chat.id)
    s.add(msg)
    s.commit()


if __name__ == '__main__':
    # if "HEROKU" in list(os.environ.keys()):
    #     logger = telebot.logger
    #     telebot.logger.setLevel(logging.INFO)
    #
    #     server = Flask(__name__)
    #
    #     @server.route("/bot", methods=['POST'])
    #     def getMessage():
    #         bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    #         return "!", 200
    #
    #     @server.route("/")
    #     def webhook():
    #         bot.remove_webhook()
    #         bot.set_webhook(
    #             url="https://min-gallows.herokuapp.com/bot")  # этот url нужно заменить на url вашего Хероку приложения
    #         return "?", 200
    #
    #
    #     server.run(host="127.0.0.1", port=os.environ.get('PORT', WEBHOOK_PORT))
    # else:
    #     # если переменной окружения HEROKU нету, значит это запуск с машины разработчика.
    #     # Удаляем вебхук на всякий случай, и запускаем с обычным поллингом.
    #     bot.remove_webhook()

        time.sleep(0.1)

        # Set webhook
        # bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH,
        #                 # certificate=open(WEBHOOK_SSL_CERT, 'r')
        #                 )

        schedule.run_pending()

        # Start flask server
        # app.run(host=WEBHOOK_LISTEN,
        #         port=WEBHOOK_PORT,
        #         #ssl_context=(WEBHOOK_SSL_CERT, WEBHOOK_SSL_PRIV),
        #         debug=True,
        #         threaded=True)

        # app.run(threaded=True)
        bot.polling()

