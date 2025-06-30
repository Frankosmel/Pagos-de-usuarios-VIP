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

bot = TeleBot(config.TOKEN, parse_mode="HTML")

selected_year = {}
selected_months = {}

def get_paid_codes_for_year(uid, year):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT periodo FROM pagos WHERE id_usuario=? AND estado='aprobado'", (uid,))
    rows = cur.fetchall(); conn.close()
    paid = set()
    for (period,) in rows:
        for tag in period.split(','):
            if '-' in tag:
                y, code = tag.split('-', 1)
                if int(y) == year:
                    paid.add(code)
    return list(paid)

@bot.message_handler(commands=["start"])
def handle_start(message):
    register_user(message.from_user)
    bot.send_message(
        message.chat.id,
        "👋 <b>Bienvenido</b> al sistema de membresías VIP.\nUsa los botones para gestionar tu suscripción.",
        parse_mode="HTML",
        reply_markup=main_menu()
    )

@bot.message_handler(func=lambda m: m.text == "💰 Pagar membresía VIP")
def handle_pay_start(message):
    uid = message.from_user.id
    register_user(message.from_user)
    bot.send_message(
        message.chat.id,
        "🔢 <b>Selecciona el año</b> para tu membresía:",
        parse_mode="HTML",
        reply_markup=year_selection_keyboard(num_years=5)
    )

@bot.callback_query_handler(func=lambda c: c.data.startswith("year_"))
def handle_year_selection(call):
    year = int(call.data.split("_",1)[1]); uid = call.from_user.id
    selected_year[uid] = year; selected_months[uid] = []
    exclude = get_paid_codes_for_year(uid, year)
    bot.edit_message_text(
        f"🗓️ <b>Meses disponibles para {year}</b>:",
        call.message.chat.id, call.message.message_id,
        parse_mode="HTML",
        reply_markup=months_selection_keyboard(year, [], exclude)
    )
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("month_"))
def handle_month_toggle(call):
    _, year_str, code = call.data.split("_",2)
    year, uid = int(year_str), call.from_user.id
    tag = f"{year}-{code}"
    sel = selected_months.setdefault(uid, [])
    if tag in sel: sel.remove(tag)
    else: sel.append(tag)
    exclude = get_paid_codes_for_year(uid, year)
    bot.edit_message_reply_markup(
        call.message.chat.id, call.message.message_id,
        reply_markup=months_selection_keyboard(year, sel, exclude)
    )
    bot.answer_callback_query(call.id, f"Seleccionados: {', '.join(sel) or 'ninguno'}")

@bot.callback_query_handler(func=lambda c: c.data == "confirm_payment")
def handle_confirm_payment(call):
    uid = call.from_user.id; codes = selected_months.get(uid, [])
    if not codes:
        return bot.answer_callback_query(call.id, "❗ Debes seleccionar al menos un mes.")
    total_days = calculate_total_days(codes)
    amount = calculate_amount(total_days, config.PRECIO_DIARIO_CUP)
    expire_date = calculate_expiration_date(codes)
    save_payment_request(uid, codes, amount)
    bot.send_message(
        call.message.chat.id,
        f"💵 <b>Resumen de tu pago</b>:\n"
        f"• Días: {total_days}\n"
        f"• Monto: {amount} CUP\n"
        f"• Vence: {expire_date}\n\n"
        "📲 Envía tu comprobante (foto o texto) para revisión.",
        parse_mode="HTML",
        reply_markup=main_menu()
    )
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data == "cancel")
def handle_cancel(call):
    uid = call.from_user.id
    selected_year.pop(uid, None); selected_months.pop(uid, None)
    bot.send_message(
        call.message.chat.id,
        "❌ Operación <b>cancelada</b>.",
        parse_mode="HTML",
        reply_markup=main_menu()
    )
    bot.answer_callback_query(call.id)

@bot.message_handler(content_types=["photo","text"])
def handle_comprobante(message):
    uid = message.from_user.id
    conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
    cur.execute(
        "SELECT id_pago, periodo, monto FROM pagos "
        "WHERE id_usuario=? AND estado='pendiente' ORDER BY fecha DESC LIMIT 1",
        (uid,)
    )
    row = cur.fetchone(); conn.close()
    if not row: return
    id_pago, period, monto = row
    caption = (
        f"🧾 <b>Nueva solicitud de pago VIP</b>\n"
        f"Usuario: @{message.from_user.username or message.from_user.first_name}\n"
        f"ID: {uid}\nPeriodo: {period}\nMonto: {monto} CUP"
    )
    if message.photo:
        fid = message.photo[-1].file_id
        bot.send_photo(config.STAFF_GROUP_ID, fid, caption=caption, reply_markup=admin_action_keyboard(uid))
        comprobante_ref = fid
    else:
        bot.send_message(config.STAFF_GROUP_ID, caption + "\n"+message.text, reply_markup=admin_action_keyboard(uid))
        comprobante_ref = message.text
    conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
    cur.execute("UPDATE pagos SET estado='en revision', comprobante=? WHERE id_pago=?", (comprobante_ref, id_pago))
    conn.commit(); conn.close()
    bot.send_message(message.chat.id, "✅ Tu comprobante fue enviado al staff.", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "📅 Ver vencimiento")
def handle_check_expiration(message):
    uid = message.from_user.id
    conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
    cur.execute("SELECT fecha_vencimiento FROM usuarios WHERE id_usuario=?", (uid,))
    row = cur.fetchone(); conn.close()
    if not row or not row[0]:
        return bot.send_message(message.chat.id, "⚠️ No tienes suscripción activa.", reply_markup=main_menu())
    exp = datetime.strptime(row[0], "%Y-%m-%d")
    days_left = (exp - datetime.now()).days
    text = (f"📅 Tu suscripción vence el <b>{exp.strftime('%d/%m/%Y')}</b>.\n"
            f"Quedan <b>{days_left} días</b> para su vencimiento.") if days_left>=0 else "⚠️ Tu suscripción ha expirado."
    bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=main_menu())

# Exportar para admin_handlers.py
user_bot = bot
