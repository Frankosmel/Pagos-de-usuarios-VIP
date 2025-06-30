# markups.py

from telebot import types

# Lista de meses con código y nombre completo
MONTHS = [
    ("ene", "Enero"), ("feb", "Febrero"), ("mar", "Marzo"),
    ("abr", "Abril"), ("may", "Mayo"), ("jun", "Junio"),
    ("jul", "Julio"), ("ago", "Agosto"), ("sep", "Septiembre"),
    ("oct", "Octubre"), ("nov", "Noviembre"), ("dic", "Diciembre")
]

def main_menu():
    """
    Teclado principal para el usuario:
    - Pagar membresía
    - Ver vencimiento
    - Cancelar acción
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("💰 Pagar membresía VIP"))
    markup.add(types.KeyboardButton("📅 Ver vencimiento"))
    markup.add(types.KeyboardButton("❌ Cancelar"))
    return markup

def months_selection_keyboard(selected=None):
    """
    Teclado inline para seleccionar meses.
    Muestra ✅ delante de los meses ya seleccionados.
    Incluye botones de Confirmar y Cancelar.
    """
    if selected is None:
        selected = []
    markup = types.InlineKeyboardMarkup(row_width=3)
    buttons = []
    for code, name in MONTHS:
        prefix = "✅ " if code in selected else ""
        # Usamos abreviatura de tres letras para el texto
        buttons.append(
            types.InlineKeyboardButton(
                f"{prefix}{name[:3]}",
                callback_data=f"month_{code}"
            )
        )
    markup.add(*buttons)
    # Botones de acción
    markup.add(
        types.InlineKeyboardButton("✅ Confirmar", callback_data="confirm_payment"),
        types.InlineKeyboardButton("❌ Cancelar", callback_data="cancel_payment")
    )
    return markup

def admin_action_keyboard(user_id):
    """
    Teclado inline para que los admins gestionen una solicitud:
    - Aprobar
    - Rechazar
    - Pedir más información
    """
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Aprobar", callback_data=f"approve_{user_id}"),
        types.InlineKeyboardButton("❌ Rechazar", callback_data=f"reject_{user_id}")
    )
    markup.add(
        types.InlineKeyboardButton("📝 Pedir más info", callback_data=f"moreinfo_{user_id}")
    )
    return markup

def cancel_keyboard():
    """
    Teclado de reply para cancelar la operación actual.
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("❌ Cancelar"))
    return markup

def back_keyboard():
    """
    Teclado de reply con opción de retroceder o cancelar.
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("⬅️ Atrás"))
    markup.add(types.KeyboardButton("❌ Cancelar"))
    return markup
