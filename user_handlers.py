# user_handlers.py

import sqlite3
from datetime import datetime
from telebot import TeleBot, types
import config
from helpers import (
    register_user,
    save_payment_request,
    calculate_total_days,
    calculate_amount,
    calculate_expiration_date,
    db as DB_PATH
)
from markups import (
    main_menu,
    year_selection_keyboard,
    months_selection_keyboard,
    admin_action_keyboard
)

# Inicializar bot
bot = TeleBot(config.TOKEN, parse_mode="HTML")

# Estados temporales por usuario
selected_year = {}       # {user_id: int}
selected_months = {}     # {user_id: ["YYYY-cc", ...]}

# --- Helpers internos ---
def get_paid_codes_for_year(uid, year):
    """
    Devuelve lista de códigos de mes ya aprobados para un usuario en un año dado.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT periodo FROM pagos WHERE id_usuario=? AND estado='aprobado'",
        (uid,)
    )
    rows = cur.fetchall()
    conn.close()
    paid = set()
    for (period,) in rows:
        for tag in period.split(','):
            if '-' in tag:
                y, code = tag.split('-', 1)
                if int(y) == year:
                    paid.add(code)
    return list(paid)

# --- Handlers de usuario ---
@bot.message_handler(commands=["start"])
def handle_start(message):
    register_user(message.from_user)
    bot.send_message(
        message.chat.id,
        "👋 <b>Bienvenido</b> al sistema de membresías VIP.\n"
        "Usa los botones para gestionar tu suscripción.",
        parse_mode="HTML",
        reply_markup=main_menu()
    )

@bot.message_handler(func=lambda m: m.text == "💰 Pagar membresía VIP")
def handle_pay_start(message):
    uid = message.from_user.id
    register_user(message.from_user)
    # Pedir selección de año
    bot.send_message(
        message.chat.id,
        "🔢 <b>Selecciona el año</b> para el pago de tu membresía:",
        parse_mode="HTML",
        reply_markup=year_selection_keyboard(num_years=5)
    )

@bot.callback_query_handler(func=lambda c: c.data.startswith("year_"))
def handle_year_selection(call):
    year = int(call.data.split("_", 1)[1])
    uid = call.from_user.id
    selected_year[uid] = year
    selected_months[uid] = []
    # Obtener meses ya pagados
    exclude = get_paid_codes_for_year(uid, year)
    bot.edit_message_text(
        f"🗓️ <b>Meses disponibles para {year}</b>:",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=months_selection_keyboard(year, [], exclude)
    )
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("month_"))
def handle_month_toggle(call):
    _, year_str, code = call.data.split("_", 2)
    year = int(year_str)
    uid = call.from_user.id
    tag = f"{year}-{code}"
    sel = selected_months.setdefault(uid, [])
    if tag in sel:
        sel.remove(tag)
    else:
        sel.append(tag)
    # Re-renderizar teclado con exclusiones
    exclude = get_paid_codes_for_year(uid, year)
    bot.edit_message_reply_markup(
        call.message.chat.id,
        call.message.message_id,
        reply_markup=months_selection_keyboard(year, sel, exclude)
    )
    bot.answer_callback_query(call.id, f"Seleccionados: {', '.join(sel) or 'ninguno'}")

@bot.callback_query_handler(func=lambda c: c.data == "confirm_payment")
def handle_confirm_payment(call):
    uid = call.from_user.id
    codes = selected_months.get(uid, [])
    if not codes:
        bot.answer_callback_query(call.id, "❗ Debes seleccionar al menos un mes.")
        return
    # Calcular totales y expiración
    total_days = calculate_total_days(codes)
    amount = calculate_amount(total_days, config.PRECIO_DIARIO_CUP)
    expire_date = calculate_expiration_date(codes)
    # Guardar solicitud
    save_payment_request(uid, codes, amount)
    # Enviar resumen al usuario
    bot.send_message(
        call.message.chat.id,
        f"💵 <b>Resumen de tu pago</b>:\n"
        f"• Días totales: {total_days}\n"
        f"• Monto: {amount} CUP\n"
        f"• Fecha de vencimiento: {expire_date}\n\n"
        "📲 Por favor envía tu comprobante (foto o texto) para revisión.",
        parse_mode="HTML",
        reply_markup=main_menu()
    )
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data == "cancel")
def handle_cancel(call):
    uid = call.from_user.id
    selected_year.pop(uid, None)
    selected_months.pop(uid, None)
    bot.send_message(
        call.message.chat.id,
        "❌ Operación <b>cancelada</b>.",
        parse_mode="HTML",
        reply_markup=main_menu()
    )
    bot.answer_callback_query(call.id)

@bot.message_handler(content_types=["photo", "text"])
def handle_comprobante(message):
    uid = message.from_user.id
    # Buscar última solicitud pendiente
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT id_pago, periodo, monto FROM pagos "
        "WHERE id_usuario=? AND estado='pendiente' ORDER BY fecha DESC LIMIT 1",
        (uid,)
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        return
    id_pago, period, monto = row
    # Preparar mensaje para staff
    caption = (
        f"🧾 <b>Nueva solicitud de pago VIP</b>\n"
        f"Usuario: @{message.from_user.username or message.from_user.first_name}\n"
        f"ID: {uid}\n"
        f"Periodo: {period}\n"
        f"Monto: {monto} CUP"
    )
    # Enviar comprobante a staff
    if message.photo:
        file_id = message.photo[-1].file_id
        bot.send_photo(
            config.STAFF_GROUP_ID,
            file_id,
            caption=caption,
            reply_markup=admin_action_keyboard(uid)
        )
        comprobante_ref = file_id
    else:
        bot.send_message(
            config.STAFF_GROUP_ID,
            caption + "\n" + message.text,
            reply_markup=admin_action_keyboard(uid)
        )
        comprobante_ref = message.text
    # Actualizar estado de solicitud
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "UPDATE pagos SET estado='en revision', comprobante=? WHERE id_pago=?",
        (comprobante_ref, id_pago)
    )
    conn.commit()
    conn.close()
    # Confirmación al usuario
    bot.send_message(
        message.chat.id,
        "✅ Tu comprobante fue enviado al staff para revisión.",
        reply_markup=main_menu()
    )

@bot.message_handler(func=lambda m: m.text == "📅 Ver vencimiento")
def handle_check_expiration(message):
    uid = message.from_user.id
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT fecha_vencimiento FROM usuarios WHERE id_usuario=?",
        (uid,)
    )
    row = cur.fetchone()
    conn.close()
    if not row or not row[0]:
        bot.send_message(
            message.chat.id,
            "⚠️ No tienes una suscripción activa.",
            reply_markup=main_menu()
        )
        return
    expire_dt = datetime.strptime(row[0], "%Y-%m-%d")
    days_left = (expire_dt - datetime.now()).days
    if days_left >= 0:
        bot.send_message(
            message.chat.id,
            f"📅 Tu suscripción vence el <b>{expire_dt.strftime('%d/%m/%Y')}</b>.\n"
            f"Quedan <b>{days_left} días</b> para su vencimiento.",
            parse_mode="HTML",
            reply_markup=main_menu()
        )
    else:
        bot.send_message(
            message.chat.id,
            "⚠️ Tu suscripción ha expirado.",
            reply_markup=main_menu()
        )

# Exportar para uso en admin_handlers.py
user_bot = bot
