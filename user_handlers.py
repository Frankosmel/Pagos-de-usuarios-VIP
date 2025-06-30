import sqlite3 from datetime import datetime token_bot = None from telebot import TeleBot, types import config from helpers import ( register_user, calculate_total_days, calculate_amount, calculate_expiration_date, save_payment_request, DB_PATH ) from markups import main_menu, months_selection_keyboard

Inicializar bot

bot = TeleBot(config.TOKEN, parse_mode="HTML")

Almacena selección de meses temporalmente: {user_id: [codes...]}

selected_months = {}

--- Handlers de usuario ---

@bot.message_handler(commands=["start"]) def handle_start(message): register_user(message.from_user) bot.send_message( message.chat.id, "👋 <b>Bienvenido</b> al sistema de membresías VIP.", reply_markup=main_menu() )

@bot.message_handler(func=lambda m: m.text == "💰 Pagar membresía VIP") def handle_pay_request(message): register_user(message.from_user) selected_months[message.from_user.id] = [] bot.send_message( message.chat.id, "🗓️ Selecciona los meses que deseas pagar:", reply_markup=months_selection_keyboard() )

@bot.callback_query_handler(func=lambda c: c.data.startswith("month_")) def handle_month_toggle(call): user_id = call.from_user.id code = call.data.split("_")[1] sel = selected_months.setdefault(user_id, []) if code in sel: sel.remove(code) else: sel.append(code) # Actualizar teclado bot.edit_message_reply_markup( call.message.chat.id, call.message.message_id, reply_markup=months_selection_keyboard(sel) ) bot.answer_callback_query(call.id, f"Meses seleccionados: {', '.join(sel) or 'ninguno'}")

@bot.callback_query_handler(func=lambda c: c.data == "confirm_payment") def handle_confirm(call): user_id = call.from_user.id codes = selected_months.get(user_id, []) if not codes: bot.answer_callback_query(call.id, "Debes seleccionar al menos un mes.") return # Calcular monto y expiración total_days = calculate_total_days(codes) amount = calculate_amount(total_days, config.PRECIO_DIARIO_CUP) expire = calculate_expiration_date(codes) # Guardar solicitud sin comprobante save_payment_request(user_id, codes, amount) # Notificar al usuario bot.send_message( call.message.chat.id, f"💵 Debes pagar <b>{amount} CUP</b> por <b>{total_days} días</b>\n" f"Tu membresía vencerá el <b>{expire}</b>.\n" "Por favor envía tu comprobante (foto o texto) aquí.", reply_markup=types.ReplyKeyboardRemove() ) bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data == "cancel_payment") def handle_cancel(call): user_id = call.from_user.id selected_months.pop(user_id, None) bot.send_message( call.message.chat.id, "❌ Operación cancelada.", reply_markup=main_menu() ) bot.answer_callback_query(call.id)

@bot.message_handler(content_types=["photo", "text"]) def handle_comprobante(message): user_id = message.from_user.id # Conectar DB para obtener último pago pendiente conn = sqlite3.connect(DB_PATH) cur = conn.cursor() cur.execute( "SELECT id_pago, periodo, monto FROM pagos " "WHERE id_usuario=? AND estado='pendiente' ORDER BY fecha DESC LIMIT 1", (user_id,) ) row = cur.fetchone() if not row: conn.close() return  # Nada que hacer id_pago, period, monto = row # Preparar caption caption = ( f"🧾 Nueva solicitud de pago VIP\n" f"Usuario: @{message.from_user.username or message.from_user.first_name}\n" f"ID: {user_id}\n" f"Período: {period}\n" f"Monto: {monto} CUP" ) # Enviar a grupo staff if message.photo: file_id = message.photo[-1].file_id bot.send_photo( config.STAFF_GROUP_ID, file_id, caption=caption ) comprobante_ref = file_id else: bot.send_message( config.STAFF_GROUP_ID, caption + "\n" + message.text ) comprobante_ref = message.text # Actualizar estado en DB cur.execute( "UPDATE pagos SET estado='en revision', comprobante=? WHERE id_pago=?", (comprobante_ref, id_pago) ) conn.commit() conn.close() # Confirmación al usuario bot.send_message( message.chat.id, "✅ Tu comprobante ha sido enviado para revisión al staff.", reply_markup=main_menu() )

@bot.message_handler(func=lambda m: m.text == "📅 Ver vencimiento") def handle_check_expiration(message): user_id = message.from_user.id conn = sqlite3.connect(DB_PATH) cur = conn.cursor() cur.execute( "SELECT fecha_vencimiento FROM usuarios WHERE id_usuario=?", (user_id,) ) row = cur.fetchone() conn.close() if not row or not row[0]: bot.send_message( message.chat.id, "⚠️ No tienes una suscripción activa.", reply_markup=main_menu() ) return expire = datetime.strptime(row[0], "%Y-%m-%d") days_left = (expire - datetime.now()).days if days_left >= 0: bot.send_message( message.chat.id, f"📅 Tu suscripción vence el <b>{expire.strftime('%d/%m/%Y')}</b>.\n" f"Quedan <b>{days_left} días</b> para su vencimiento.", reply_markup=main_menu() ) else: bot.send_message( message.chat.id, "⚠️ Tu suscripción ha expirado.", reply_markup=main_menu() )

Exportar bot para import en admin_handlers.py

user_bot = bot

