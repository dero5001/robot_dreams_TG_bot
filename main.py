import telebot
import sqlite3
import requests
import json
from telebot import types


bot = telebot.TeleBot('5807577688:AAEgDUJMILd85vMdAnMvRnY92TV_R4gZW9w')
weather_api = 'c5afed9d8d2565153d5d267f5acd0680'


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, f"Hello {message.from_user.first_name}, I am a Roman Denysiuk's final tusk bot")
    bot.send_message(message.chat.id, 'You can use /commands to see the commands list')


@bot.message_handler(commands=['commands'])
def commands(message):
    bot.send_message(
        message.chat.id,
        'You can use next functions:\n'
        ' - /start - Shows the start info\n'
        ' - /commands - Shows the list of active commands\n'
        ' - /tellist - To edit the contact book\n'
        ' - /get_weather - Choose a city and get the weather info\n'
        ' - /exchange_rate - Check the exchange rate for USD, EUR, BTC and ETH'
    )


@bot.message_handler(commands=['get_weather'])
def get_weather(message):
    bot.send_message(message.chat.id, 'Please enter a city name')
    bot.register_next_step_handler_by_chat_id(message.chat.id, weather_request)


@bot.message_handler(commands=['exchange_rate'])
def handle_currencies(message):

    markup = telebot.types.InlineKeyboardMarkup(row_width=2)

    button_1 = telebot.types.InlineKeyboardButton('USD UAH rate', callback_data='usd_uah')
    button_2 = telebot.types.InlineKeyboardButton('EUR UAH rate', callback_data='eur_uah')
    button_3 = telebot.types.InlineKeyboardButton('BTC USD rate', callback_data='btc_usd')
    button_4 = telebot.types.InlineKeyboardButton('ETH USD rate', callback_data='eth_usd')
    markup.add(button_1, button_2, button_3, button_4)

    bot.send_message(message.from_user.id, "Please select the required currencies:", reply_markup=markup)


@bot.message_handler(commands=['tellist'])
def tellist(message):

    connection = sqlite3.connect('tellist_db.sql')
    cur = connection.cursor()
    table_name = f'{message.from_user.id}'

    cur.execute("CREATE TABLE IF NOT EXISTS '%s' (Id INTEGER NOT NULL PRIMARY KEY, Name varchar(100), Tel_number varchar(13))" % (table_name))
    connection.commit()
    cur.close()
    connection.close()

    markup = types.InlineKeyboardMarkup()
    button_1 = types.InlineKeyboardButton('Check a phone book', callback_data='check_list')
    button_2 = types.InlineKeyboardButton('Delete a contact', callback_data='delete')
    button_3 = types.InlineKeyboardButton('Add a contact', callback_data='add')
    markup.row(button_1)
    markup.row(button_2, button_3)

    bot.send_message(message.chat.id, 'Please check what do you need', reply_markup=markup)


@bot.callback_query_handler(func=lambda callback: True)
def callback_message(callback):
    if callback.data == 'check_list':

        connection = sqlite3.connect('tellist_db.sql')
        cur = connection.cursor()
        table_name = f'{callback.from_user.id}'
        cur.execute("SELECT * FROM '%s'" % table_name)

        records_list = cur.fetchall()
        requested_info = ''
        for record in records_list:
            requested_info += f'- Name: {record[1]}, Number: {record[2]} ID: {record[0]}\n'

        cur.close()
        connection.close()

        bot.send_message(callback.from_user.id, requested_info)

    elif callback.data == 'delete':

        bot.send_message(callback.from_user.id, 'Enter the ID of a contact that you want to delete')
        bot.register_next_step_handler_by_chat_id(callback.from_user.id, delete_record)

    elif callback.data == 'add':
        bot.send_message(callback.from_user.id, 'Please enter the contact name')
        bot.register_next_step_handler_by_chat_id(callback.from_user.id, add_record)

    elif callback.data == 'usd_uah':
        response = requests.get('https://api.exchangerate-api.com/v4/latest/USD')
        data = response.json()
        rate = data['rates']['UAH']
        result_message = f"UAH/USD rate: {rate}"
        bot.send_message(callback.from_user.id, result_message)

    elif callback.data == 'eur_uah':
        response = requests.get('https://api.exchangerate-api.com/v4/latest/EUR')
        data = response.json()
        rate = data['rates']['UAH']
        result_message = f"UAH/EUR rate: {rate}"
        bot.send_message(callback.from_user.id, result_message)

    elif callback.data == 'btc_usd':
        response = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd')
        data = response.json()
        rate = data['bitcoin']['usd']
        result_message = f"BTC/USD rate: {rate}"
        bot.send_message(callback.from_user.id, result_message)

    elif callback.data == 'eth_usd':
        response = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd')
        data = response.json()
        rate = data['ethereum']['usd']
        result_message = f"ETH/USD rate: {rate}"
        bot.send_message(callback.from_user.id, result_message)

    else:
        bot.send_message(callback.from_user.id, 'Bad request.')


def weather_request(callback):
    city = callback.text.strip().lower()
    weather_info = requests.get(f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={weather_api}&units=metric')
    if weather_info.status_code == 200:
        data = json.loads(weather_info.text)
        weather = data["weather"][0]["main"]
        temperature = data["main"]["temp"]

        bot.reply_to(callback, f'There is {weather}, and the temperature is: {temperature} °C')
    else:
        bot.reply_to(callback, 'You enter a wrong city name')


def add_record(callback):
    global record_name
    record_name = '' #To avoid double name creation
    record_name += callback.text

    bot.send_message(callback.from_user.id, 'Please enter the contact number')
    bot.register_next_step_handler_by_chat_id(callback.from_user.id, add_number)


def add_number(callback):
    if callback.text.isdigit():

        connection = sqlite3.connect('tellist_db.sql')
        cur = connection.cursor()
        table_name = f'{callback.from_user.id}'

        cur.execute(
            "INSERT INTO '%s' (name, tel_number) VALUES ('%s', '%s')" % (table_name, record_name, callback.text)
        )
        connection.commit()
        cur.close()
        connection.close()

        bot.send_message(callback.from_user.id, f'Contact "{record_name}" with number {callback.text} created')
    else:
        bot.send_message(callback.from_user.id, 'Only numbers required. Please try again')


def delete_record(callback):
    delete_target = callback.text

    connection = sqlite3.connect('tellist_db.sql')
    cur = connection.cursor()
    table_name = f'{callback.from_user.id}'

    cur.execute(
        "DELETE FROM '%s' WHERE ID='%s'" % (table_name, delete_target)
    )
    connection.commit()
    cur.close()
    connection.close()

    bot.send_message(callback.from_user.id, 'Deleted')


bot.polling(none_stop=True)
