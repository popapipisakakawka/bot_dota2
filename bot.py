

import telebot
from telebot import types
import random
import os

TOKEN = "8223594376:AAH4KZuIa5N0Tz8hzOj3Fp7yizC9BLGcIPc"
bot = telebot.TeleBot(TOKEN)


HEROES_FOLDER = "heroes"
SPY_IMAGE = "spy.jpg"

games = {}

KARAKOZ_FOLDER = os.path.join(os.path.dirname(__file__), "karakoz")


@bot.message_handler(commands=['karakoz'])
def karakoz(message):
    photos = [f for f in os.listdir(KARAKOZ_FOLDER) if f.lower().endswith(('.jpg', '.png'))]

    photo_file = os.path.join(KARAKOZ_FOLDER, random.choice(photos))

    with open(photo_file, 'rb') as photo:
        bot.send_photo(message.chat.id, photo)



@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🎮 Начать игру", callback_data="start_game"))
    bot.send_message(message.chat.id,
                     "Добро пожаловать в игру *Шпион (Dota 2)*",
                     parse_mode="Markdown",
                     reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "start_game")
def start_game(call):
    bot.send_message(call.message.chat.id, "👥 Сколько игроков? (введи число)")
    bot.register_next_step_handler(call.message, set_players)


def set_players(message):
    if not message.text.isdigit():
        bot.send_message(message.chat.id, "❌ Нужно ввести число")
        return

    players = int(message.text)
    if players < 3:
        bot.send_message(message.chat.id, "❌ Минимум 3 игрока")
        return

    hero_images = [f for f in os.listdir(HEROES_FOLDER)
                   if f.endswith('.jpg') or f.endswith('.png')]

    hero_image = random.choice(hero_images)  # ОДИН герой на всю игру
    spy_index = random.randint(1, players)

    games[message.chat.id] = {
        "players": players,
        "current": 1,
        "spy_index": spy_index,
        "hero_image": hero_image,
        "last_photo_id": None,
        "last_control_msg_id": None,
        "last_info_msg_id": None
    }

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("👁 Показать героя", callback_data="show_hero"))

    info_msg = bot.send_message(
        message.chat.id,
        "🚫 Убери даунов от экрана😄 Передай телефон игроку №1",
        reply_markup=markup
    )

    games[message.chat.id]["last_info_msg_id"] = info_msg.message_id


@bot.callback_query_handler(func=lambda call: call.data == "show_hero")
def show_hero(call):
    game = games.get(call.message.chat.id)
    if not game:
        return


    if game.get("last_info_msg_id"):
        try:
            bot.delete_message(call.message.chat.id, game["last_info_msg_id"])
        except:
            pass
        game["last_info_msg_id"] = None

    current = game["current"]

    if current == game["spy_index"]:
        photo = open(SPY_IMAGE, "rb")
        msg = bot.send_photo(
            call.message.chat.id,
            photo,
            caption="🕵️‍♂️ *ТЫ ШПИОН*",
            parse_mode="Markdown"
        )
    else:
        hero = game["hero_image"]
        photo = open(os.path.join(HEROES_FOLDER, hero), "rb")
        msg = bot.send_photo(
            call.message.chat.id,
            photo,
            caption="🦸‍♂️ *ТВОЙ ГЕРОЙ*",
            parse_mode="Markdown"
        )

    game["last_photo_id"] = msg.message_id

    #
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        "➡️ Следующий игрок",
        callback_data="next_player"
    ))

    control_msg = bot.send_message(
        call.message.chat.id,
        "Передай телефон следующему игроку",
        reply_markup=markup
    )
    game["last_control_msg_id"] = control_msg.message_id

@bot.callback_query_handler(func=lambda call: call.data == "next_player")
def next_player(call):
    game = games.get(call.message.chat.id)
    if not game:
        return


    if game.get("last_photo_id"):
        try:
            bot.delete_message(call.message.chat.id, game["last_photo_id"])
        except:
            pass

    if game.get("last_control_msg_id"):
        try:
            bot.delete_message(call.message.chat.id, game["last_control_msg_id"])
        except:
            pass

    game["current"] += 1

    if game["current"] > game["players"]:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔁 Начать новую игру", callback_data="start_game"))
        bot.send_message(call.message.chat.id,
                         "✅ Все роли розданы! Можно начинать игру 🎉",
                         reply_markup=markup)
        del games[call.message.chat.id]
        return

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("👁 Показать героя", callback_data="show_hero"))

    info_msg = bot.send_message(call.message.chat.id,
                     f"🚫 УБЕРИ ДАУНОВ ОТ ЭКРАНА 😄"

                     f"Передай телефон игроку №{game['current']}",
                     reply_markup=markup)
    game["last_info_msg_id"] = info_msg.message_id

bot.infinity_polling()
