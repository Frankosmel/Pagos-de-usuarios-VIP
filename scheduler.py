import sqlite3 from datetime import datetime, timedelta from apscheduler.schedulers.background import BackgroundScheduler import config from user_handlers import user_bot as bot from markups import main_menu

DB_PATH = 'bot.db'

def reminders_days_before(): """ Envía recordatorios a usuarios y admins DIAS_RECORDATORIO días antes del vencimiento. """ conn = sqlite3.connect(DB_PATH) cur = conn.cursor() # Fecha objetivo: hoy + DIAS_RECORDATORIO días target_date = (datetime.now().date() + timedelta(days=config.DIAS_RECORDATORIO)).strftime('%Y-%m-%d') cur.execute("SELECT id_usuario, fecha_vencimiento FROM usuarios WHERE fecha_vencimiento = ?", (target_date,)) users = cur.fetchall() conn.close()

if not users:
    return

# Notificar a cada usuario
for uid, fecha in users:
    fecha_fmt = datetime.strptime(fecha, '%Y-%m-%d').strftime('%d/%m/%Y')
    bot.send_message(
        uid,
        f"🕒 Recordatorio: tu suscripción vence en {config.DIAS_RECORDATORIO} días, el {fecha_fmt}.",
        reply_markup=main_menu()
    )

# Notificar a administradores
text = f"📢 <b>Usuarios con vencimiento en {config.DIAS_RECORDATORIO} días:</b>\n"
for uid, fecha in users:
    text += f"- {uid} (vence {datetime.strptime(fecha, '%Y-%m-%d').strftime('%d/%m/%Y')})\n"
for admin in config.ADMIN_IDS:
    bot.send_message(admin, text, parse_mode="HTML")

def reminders_hours_before(): """ Envía recordatorios a usuarios HORAS_RECORDATORIO horas antes del vencimiento. """ conn = sqlite3.connect(DB_PATH) cur = conn.cursor() cur.execute("SELECT id_usuario, fecha_vencimiento FROM usuarios") rows = cur.fetchall() conn.close()

now = datetime.now()
for uid, fecha in rows:
    dt = datetime.strptime(fecha, '%Y-%m-%d')
    delta = dt - now
    if timedelta(0) < delta <= timedelta(hours=config.HORAS_RECORDATORIO):
        hours_left = int(delta.total_seconds() // 3600)
        bot.send_message(
            uid,
            f"⏰ Recordatorio: tu suscripción vence en {hours_left} horas ({dt.strftime('%d/%m/%Y')}). ¡No olvides renovar!",
            reply_markup=main_menu()
        )

def start_scheduler(): """ Inicializa el scheduler con jobs para recordatorios diarios y horarios. """ scheduler = BackgroundScheduler() # Job diario a las 09:00 scheduler.add_job(reminders_days_before, 'cron', hour=9, minute=0) # Job cada hora scheduler.add_job(reminders_hours_before, 'interval', hours=1) scheduler.start() print("✅ Scheduler iniciado.")

