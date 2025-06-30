# bot.py

import telebot
from telebot import types
from database import init_db
import config

# inicializar base de datos
init_db()

# inicializar bot
bot = telebot.TeleBot(config.TOKEN, parse_mode="HTML")

# comando /start
@bot.message_handler(commands=["start"])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("💰 Pagar membresía VIP"))
    bot.send_message(
        message.chat.id,
        "👋 <b>Bienvenido</b> al sistema de membresías VIP.\n\n"
        "Usa el botón para gestionar tu suscripción o pagar tu membresía.",
        reply_markup=markup
    )

# en el siguiente paso agregaremos handlers completos de usuarios y admin
# por ahora dejamos el polling
print("✅ Bot en ejecución...")
bot.infinity_polling()
