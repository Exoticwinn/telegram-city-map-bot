import telebot
from telebot import types
from config import *
from logic import *

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(message.chat.id, "Привет! Я бот, который может показывать города на карте. Напиши /help для списка команд.")

@bot.message_handler(commands=['help'])
def handle_help(message):
    bot.send_message(message.chat.id, "Доступные команды:  \n/start - начать работу с ботом\n/help - показать список команд\n/show_city <city_name> - показать город на карте\n/show_country_cities <country> - показать города страны\n/set_color - выбрать цвет маркеров\n/remember_city <city_name> - сохранить город в список посещенных\n/show_my_cities - показать все сохраненные города")


@bot.message_handler(commands=['show_country_cities'])
def handle_show_country_cities(message):
    country = message.text.partition(" ")[2].strip()
    if not country:
        bot.send_message(
            message.chat.id,
            "Укажите страну на английском: /show_country_cities <country>"
        )
        return

    cities = manager.select_cities_by_country(country)
    if not cities:
        bot.send_message(message.chat.id, f"Не нашёл города в стране «{country}».")
        return

    prefix = f"Города страны {country}:\n"
    chunk = prefix
    for city in cities:
        line = f"• {city}\n"
        if len(chunk) + len(line) > 3500:
            bot.send_message(message.chat.id, chunk.rstrip())
            chunk = ""
        chunk += line
    if chunk:
        bot.send_message(message.chat.id, chunk.rstrip())


@bot.message_handler(commands=['show_city'])
def handle_show_city(message):
    city_name = message.text.partition(" ")[2].strip()
    if not city_name:
        bot.send_message(message.chat.id, "Укажите город: /show_city <city_name>")
        return

    user_id = message.chat.id
    if not manager.get_coordinates(city_name):
        bot.send_message(message.chat.id, f"Город {city_name} не найден. Проверьте написание на английском.")
        return

    manager.create_grapf(
        f"{user_id}.png",
        [city_name],
        marker_color=manager.get_marker_color(user_id)
    )

    with open(f"{user_id}.png", "rb") as map:
        bot.send_photo(user_id, map)


@bot.message_handler(commands=['set_color'])
def handle_set_color(message):
    keyboard = types.InlineKeyboardMarkup()
    buttons = [
        types.InlineKeyboardButton(label, callback_data=f"marker_color:{color}")
        for label, color in DB_Map.MARKER_COLORS.items()
    ]
    for index in range(0, len(buttons), 2):
        keyboard.row(*buttons[index:index + 2])
    bot.send_message(message.chat.id, "Выберите цвет маркеров на карте:", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data and call.data.startswith("marker_color:"))
def handle_marker_color_selection(call):
    marker_color = call.data.partition(":")[2]
    if marker_color not in DB_Map.MARKER_COLORS.values():
        bot.answer_callback_query(call.id, "Неизвестный цвет.")
        return

    user_id = call.message.chat.id
    manager.set_marker_color(user_id, marker_color)
    color_name = next(
        label for label, color in DB_Map.MARKER_COLORS.items()
        if color == marker_color
    )
    bot.answer_callback_query(call.id, f"Выбран цвет: {color_name}")
    bot.send_message(user_id, f"Цвет маркеров изменён на «{color_name}».")


@bot.message_handler(commands=['remember_city'])
def handle_remember_city(message):
    user_id = message.chat.id
    city_name = message.text.split()[-1]
    if manager.add_city(user_id, city_name):
        bot.send_message(message.chat.id, f'Город {city_name} успешно сохранен!')
    else:
        bot.send_message(message.chat.id, 'Такого города я не знаю. Убедись, что он написан на английском!')

@bot.message_handler(commands=['show_my_cities'])
def handle_show_visited_cities(message):
    cities = manager.select_cities(message.chat.id)
    if cities:
        bot.send_message(message.chat.id, "Ваши сохраненные города: " + ", ".join(cities))
    else:
        bot.send_message(message.chat.id, "Нету сохраненных городов.")


if __name__=="__main__":
    manager = DB_Map(DATABASE)
    manager.create_user_table()
    bot.polling()
