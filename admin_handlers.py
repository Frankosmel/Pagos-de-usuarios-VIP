import sqlite3
from datetime import datetime
from telebot import types
import config
from helpers import log_action, register_user, DB_PATH
from markups import admin_action_keyboard, main_menu
from user_handlers import user_bot

bot = user_bot  # reutilizamos la instancia del bot

# --- Handlers de administración ---
@bot.callback_query_handler(func=lambda c: c.data.startswith("approve_"))
def handle_approve(call):
    # Extraer user_id
    user_id = int(call.data.split("_")[1])
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    # Actualizar pago y usuario
    cur.execute(
        "UPDATE pagos SET estado='aprobado' WHERE id_usuario=? AND estado='en revision'",
        (user_id,)
    )
    # Calcular fecha de expiración y actualizar en usuarios
    cur.execute(
        "SELECT periodo FROM pagos WHERE id_usuario=? ORDER BY fecha DESC LIMIT 1", (user_id,)
    )
    periodo = cur.fetchone()[0].split(',')
    # Importar función de helpers para expiración
    from helpers import calculate_expiration_date
    expire_date = calculate_expiration_date(periodo)
    cur.execute(
        "INSERT OR REPLACE INTO usuarios (id_usuario, fecha_vencimiento) VALUES (?, ?)", 
        (user_id, expire_date)
    )
    conn.commit()
    conn.close()

    # Notificaciones
    bot.send_message(user_id, f"✅ ¡Tu membresía VIP ha sido <b>aprobada</b>!\nVálida hasta: {expire_date}", parse_mode="HTML", reply_markup=main_menu())
    bot.send_message(config.STAFF_GROUP_ID, f"✅ Solicitud de pago aprobada para <b>{user_id}</b>.", parse_mode="HTML")
    log_action(f"Pago aprobado: {user_id}")
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("reject_"))
def handle_reject(call):
    user_id = int(call.data.split("_")[1])
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    # Actualizar estado
    cur.execute(
        "UPDATE pagos SET estado='rechazado' WHERE id_usuario=? AND estado='en revision'",
        (user_id,)
    )
    conn.commit()
    conn.close()

    # Notificaciones
    bot.send_message(user_id, "❌ Tu solicitud de pago ha sido <b>rechazada</b>. Por favor contacta al soporte.", parse_mode="HTML", reply_markup=main_menu())
    bot.send_message(config.STAFF_GROUP_ID, f"❌ Solicitud de pago rechazada para <b>{user_id}</b>.", parse_mode="HTML")
    log_action(f"Pago rechazado: {user_id}")
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("moreinfo_"))
def handle_moreinfo(call):
    user_id = int(call.data.split("_")[1])
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    # Cambiar estado a pendiente info
    cur.execute(
        "UPDATE pagos SET estado='pendiente info' WHERE id_usuario=? AND estado='en revision'",
        (user_id,)
    )
    conn.commit()
    conn.close()

    # Notificaciones
    bot.send_message(user_id, "📝 Por favor envía documentación adicional para completar tu solicitud.", reply_markup=main_menu())
    bot.send_message(config.STAFF_GROUP_ID, f"📝 Se solicitó más información a <b>{user_id}</b>.", parse_mode="HTML")
    log_action(f"Más info solicitada: {user_id}")
    bot.answer_callback_query(call.id)

# Comando para que admins vean lista de pagos pendientes
@bot.message_handler(commands=["pendientes"])
def handle_list_pending(message):
    if message.from_user.id not in config.ADMIN_IDS:
        return
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id_pago, id_usuario, periodo, monto FROM pagos WHERE estado='pendiente' ORDER BY fecha DESC")
    rows = cur.fetchall()
    conn.close()
    if not rows:
        bot.send_message(message.chat.id, "✅ No hay solicitudes de pago pendientes.")
        return
    text = "📋 *Solicitudes Pendientes:*\n"
    for pid, uid, period, amount in rows:
        text += f"\n• ID Pago: `{pid}`, Usuario: `{uid}`, Periodo: {period}, Monto: {amount} CUP"
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

# Exportar bot
admin_bot = bot
