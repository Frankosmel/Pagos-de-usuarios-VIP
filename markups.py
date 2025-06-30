# markups.py

from datetime import datetime
from telebot import types

# Lista de meses y sus nombres completos
MONTHS = [
    ("ene", "Enero"), ("feb", "Febrero"), ("mar", "Marzo"),
    ("abr", "Abril"), ("may", "Mayo"), ("jun", "Junio"),
    ("jul", "Julio"), ("ago", "Agosto"), ("sep", "Septiembre"),
    ("oct", "Octubre"), ("nov", "Noviembre"), ("dic", "Diciembre")
]

# --- Teclados principales ---
def main_menu():
    """
    🏠 Teclado principal para el bot:
    - 💰 Pagar membresía VIP
    - 📅 Ver vencimiento
    - ❌ Cancelar
    """
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(types.KeyboardButton("💰 Pagar membresía VIP"))
    kb.add(types.KeyboardButton("📅 Ver vencimiento"))
    kb.add(types.KeyboardButton("❌ Cancelar"))
    return kb

# --- Selección de año y meses ---
def year_selection_keyboard(num_years=3):
    """
    🔢 Inline keyboard para elegir el año de la membresía.
    Genera botones desde el año actual hasta + num_years.
    """
    current = datetime.now().year
    years = [current + i for i in range(num_years)]
    kb = types.InlineKeyboardMarkup(row_width=2)
    for y in years:
        kb.add(types.InlineKeyboardButton(str(y), callback_data=f"year_{y}"))
    kb.add(types.InlineKeyboardButton("❌ Cancelar", callback_data="cancel"))
    return kb

def months_selection_keyboard(year, selected=None, exclude=None):
    """
    📆 Inline keyboard para seleccionar meses de un año específico.
    - year: año seleccionado (int)
    - selected: lista de etiquetas "YYYY-cc" ya marcados
    - exclude: lista de códigos de mes que ya están pagados (se ocultan)
    """
    if selected is None:
        selected = []
    if exclude is None:
        exclude = []

    kb = types.InlineKeyboardMarkup(row_width=3)
    for code, name in MONTHS:
        if code in exclude:
            continue
        tag = f"{year}-{code}"
        prefix = "✅ " if tag in selected else ""
        kb.add(types.InlineKeyboardButton(f"{prefix}{name[:3]}", callback_data=f"month_{year}_{code}"))

    # Si no hay meses disponibles
    if all(code in exclude for code, _ in MONTHS):
        kb.add(types.InlineKeyboardButton("ℹ️ Nada por pagar", callback_data="none"))

    # Botones de acción
    kb.add(
        types.InlineKeyboardButton("✅ Confirmar", callback_data="confirm_payment"),
        types.InlineKeyboardButton("❌ Cancelar", callback_data="cancel")
    )
    return kb

# --- Teclados de administración ---
def admin_action_keyboard(user_id):
    """
    👮 Inline keyboard para que los admins gestionen una solicitud:
    - Aprobar
    - Rechazar
    - Pedir más info
    """
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("✅ Aprobar", callback_data=f"approve_{user_id}"),
        types.InlineKeyboardButton("❌ Rechazar", callback_data=f"reject_{user_id}")
    )
    kb.add(types.InlineKeyboardButton("📝 Pedir más info", callback_data=f"moreinfo_{user_id}"))
    return kb
