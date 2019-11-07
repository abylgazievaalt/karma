import datetime
import psycopg2
import telebot
import inline_calendar

from sqlalchemy.orm import sessionmaker
from telebot import types
from config import TOKEN
from crud import engine, recreate_database
from models import User, Message1

# Base.metadata.create_all(engine)

current_shown_dates = {}
recreate_database()

Session = sessionmaker(bind=engine)
s = Session()


bot = telebot.TeleBot(TOKEN)

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

@bot.message_handler(commands=['busyfromto'])
def busy_from(message):
    markup = types.ForceReply(selective=False)
    reply_msg = bot.send_message(chat_id=message.chat.id, text="Enter start date", reply_markup=markup)
    bot.register_next_step_handler(reply_msg, savedatefrom)

def savedatefrom(message):
    chat_id = message.chat.id
    msg = Message1(update_id=message.message_id, text=message.text, sender_id=message.from_user.id)
    date = msg.text
    list = date.split('/', maxsplit=2)
    busy_from = datetime.datetime(int(list[2]), int(list[1]), int(list[0]))
    user_id = message.from_user.id
    user = s.query(User).get(message.from_user.id)
    user.busy_from_date = busy_from
    s.add(user)
    s.commit()
    markup = types.ForceReply(selective=False)
    reply_msg = bot.send_message(chat_id=message.chat.id, text="Enter deadline date", reply_markup=markup)
    bot.register_next_step_handler(reply_msg, savedateto)

def savedateto(message):
    chat_id = message.chat.id
    msg = Message1(update_id=message.message_id, text=message.text, sender_id=message.from_user.id)
    date = msg.text
    list = date.split('/', maxsplit=2)
    busy_to = datetime.datetime(int(list[2]), int(list[1]), int(list[0]))
    user_id = message.from_user.id
    user = s.query(User).get(message.from_user.id)
    user.busy_to_date = busy_to
    s.add(user)
    s.commit()

'''
@bot.message_handler(commands=['calendar'])
def handle_calendar_command(message):

    now = datetime.datetime.now()
    chat_id = message.chat.id

    date = (now.year, now.month)
    current_shown_dates[chat_id] = date

    markup = create_calendar(now.year, now.month)

    bot.send_message(message.chat.id, "Please, choose a date", reply_markup=markup)


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

'''
'''
@bot.message_handler(commands=['calendar'])
def calendar_test(msg: types.Message):
    inline_calendar.init(msg.from_user.id,
                         datetime.date.today(),
                         datetime.date(year=2018, month=11, day=1),
                         datetime.date(year=2019, month=4, day=1))
    bot.send_message(msg.from_user.id, text='test', reply_markup=inline_calendar.get_keyboard(msg.from_user.id))


@bot.callback_query_handler(func=inline_calendar.is_inline_calendar_callbackquery)
def calendar_callback_handler(q: types.CallbackQuery):
    bot.answer_callback_query(q.id)

    try:
        return_data = inline_calendar.handler_callback(q.from_user.id, q.data)
        if return_data is None:
            bot.edit_message_reply_markup(chat_id=q.from_user.id, message_id=q.message.message_id,
                                          reply_markup=inline_calendar.get_keyboard(q.from_user.id))
        else:
            picked_data = return_data
            bot.edit_message_text(text=picked_data, chat_id=q.from_user.id, message_id=q.message.message_id,
                                  reply_markup=inline_calendar.get_keyboard(q.from_user.id))

    except inline_calendar.WrongChoiceCallbackException:
        bot.edit_message_text(text='Wrong choice', chat_id=q.from_user.id, message_id=q.message.message_id,
                              reply_markup=inline_calendar.get_keyboard(q.from_user.id))
'''

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

    user_id = message.from_user.id
    user = s.query(User).get(message.from_user.id)

    if records[0][0] > 15:
        bot.reply_to(message, ('Activity: normal = {}, messages = %d'%records[0][0]).format(normal))
        user.activity = 2
    elif records[0][0] > 30:
        bot.reply_to(message, ('Activity: high = {}, messages = %d'%records[0][0]).format(high))
        user.activity = 4
    else:
        bot.reply_to(message, ('Activity: low = {}, messages = %d'%records[0][0]).format(low))


@bot.message_handler(commands=['getbusypoints'])
def get_users(message):
    #connection = psycopg2.connect(user="postgres", password="Anbanb201299", host="localhost",
    #                              port="5432", database="finalBotDb")
    #cursor = connection.cursor()
    #mes_id = message.from_user.id
    #cursor.execute("select count(*) from message where sender_id = '%s'", [mes_id])
    #records = cursor.fetchall()

    user_id = message.from_user.id
    user = s.query(User).get(message.from_user.id)

    date_from = user.busy_from_date
    date_to = user.busy_to_date
    now = datetime.datetime.now()
    date = date_from - date_to
    #for i in
    #dif = 0
    if (date_to and date_to > now):
        dif = now - date_from

    print(dif)


@bot.message_handler(commands=['getpoints'])
def get_users(message):
    connection = psycopg2.connect(user="postgres", password="Anbanb201299", host="localhost",
                                  port="5432", database="finalBotDb")
    cursor = connection.cursor()
    mes_id = message.from_user.id
    cursor.execute("select count(*) from message where sender_id = '%s'", [mes_id])
    records = cursor.fetchall()


@bot.message_handler(func=lambda message: True)
def upper(message: telebot.types.Message):
    msg = Message1(update_id=message.message_id, text=message.text, sender_id=message.from_user.id,
                   chat_id=message.chat.id)
    s.add(msg)
    s.commit()


bot.polling()

while True:
    pass
