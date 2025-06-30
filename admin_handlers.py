# admin_handlers.py

import sqlite3
from datetime import datetime
from telebot import types
import config
from helpers import log_action, register_user, db as DB_PATH
from markups import admin_action_keyboard, main_menu
from user_handlers import user_bot as bot

@bot.callback_query_handler(func=lambda c: c.data.startswith("approve_"))
def handle_approve(call):
    uid = int(call.data.split("_",1)[1])
    conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
    cur.execute("UPDATE pagos SET estado='aprobado' WHERE id_usuario=? AND estado='en revision'", (uid,))
    cur.execute("SELECT periodo FROM pagos WHERE id_usuario=? ORDER BY fecha DESC LIMIT 1", (uid,))
    period = cur.fetchone()[0].split(",")
    from helpers import calculate_expiration_date
    new_expire = calculate_expiration_date(period)
    cur.execute("UPDATE usuarios SET fecha_vencimiento=?, estado='activo' WHERE id_usuario=?", (new_expire, uid))
    conn.commit(); conn.close()
    bot.send_message(uid, f"✅ <b>¡Pago aprobado!</b>\nTu membresía VIP vence: {new_expire}", parse_mode="HTML", reply_markup=main_menu())
    bot.send_message(config.STAFF_GROUP_ID, f"✅ Aprobado para <b>{uid}</b> (vence {new_expire})", parse_mode="HTML")
    log_action(f"Pago aprobado: {uid}")
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("reject_"))
def handle_reject(call):
    uid = int(call.data.split("_",1)[1])
    conn=sqlite3.connect(DB_PATH); cur=conn.cursor()
    cur.execute("UPDATE pagos SET estado='rechazado' WHERE id_usuario=? AND estado='en revision'", (uid,))
    conn.commit(); conn.close()
    bot.send_message(uid, "❌ <b>Tu pago ha sido rechazado.</b>\nRevisa tu comprobante o contacta soporte.", parse_mode="HTML", reply_markup=main_menu())
    bot.send_message(config.STAFF_GROUP_ID, f"❌ Rechazado para <b>{uid}</b>.", parse_mode="HTML")
    log_action(f"Pago rechazado: {uid}")
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("moreinfo_"))
def handle_moreinfo(call):
    uid = int(call.data.split("_",1)[1])
    conn=sqlite3.connect(DB_PATH); cur=conn.cursor()
    cur.execute("UPDATE pagos SET estado='pendiente info' WHERE id_usuario=? AND estado='en revision'", (uid,))
    conn.commit(); conn.close()
    bot.send_message(uid, "📝 <b>Por favor envía documentación adicional.</b>", parse_mode="HTML", reply_markup=main_menu())
    bot.send_message(config.STAFF_GROUP_ID, f"📝 Más info solicitada a <b>{uid}</b>.", parse_mode="HTML")
    log_action(f"Más info solicitada: {uid}")
    bot.answer_callback_query(call.id)

@bot.message_handler(commands=["pendientes"])
def handle_list_pending(message):
    if message.from_user.id not in config.ADMIN_IDS:
        return
    conn=sqlite3.connect(DB_PATH); cur=conn.cursor()
    cur.execute("SELECT id_pago, id_usuario, periodo, monto FROM pagos WHERE estado='pendiente' ORDER BY fecha DESC")
    rows=cur.fetchall(); conn.close()
    if not rows:
        return bot.send_message(message.chat.id, "✅ No hay solicitudes pendientes.")
    text="📋 <b>Solicitudes pendientes:</b>\n"
    for pid, uid, period, amount in rows:
        text+=f"\n• Pago {pid} · Usuario {uid} · Periodo:{period} · Monto:{amount} CUP"
    bot.send_message(message.chat.id, text, parse_mode="HTML")
