helpers.py

import sqlite3 import calendar from datetime import datetime from telebot.types import User

from markups import MONTHS

DB_PATH = 'bot.db'

--- Cálculos de fechas y montos ---

def month_code_to_int(code): """Convierte código de mes ("ene") a número de mes (1=enero).""" codes = [c for c, _ in MONTHS] return codes.index(code) + 1

def days_in_month(code, year=None): """Devuelve la cantidad de días del mes dado para el año especificado (por defecto el actual).""" if year is None: year = datetime.now().year month = month_code_to_int(code) return calendar.monthrange(year, month)[1]

def calculate_total_days(codes, year=None): """Suma los días de todos los códigos de mes proporcionados.""" return sum(days_in_month(c, year) for c in codes)

def calculate_amount(total_days, price_per_day): """Calcula el monto total a pagar.""" return total_days * price_per_day

def calculate_expiration_date(codes, year=None): """Calcula la fecha de vencimiento: último día del último mes seleccionado.""" if year is None: year = datetime.now().year code_order = [c for c, _ in MONTHS] sorted_codes = sorted(codes, key=lambda c: code_order.index(c)) last = sorted_codes[-1] month = month_code_to_int(last) last_day = calendar.monthrange(year, month)[1] return datetime(year, month, last_day).strftime('%Y-%m-%d')

def format_date(date_str, fmt_in="%Y-%m-%d", fmt_out="%d/%m/%Y"): """Formatea una fecha de un formato a otro.""" dt = datetime.strptime(date_str, fmt_in) return dt.strftime(fmt_out)

--- Funciones de base de datos ---

def _connect(): return sqlite3.connect(DB_PATH)

def log_action(action): """Inserta un registro en la tabla de logs.""" conn = _connect() cur = conn.cursor() cur.execute( "INSERT INTO log (accion, fecha) VALUES (?, datetime('now','localtime'))", (action,) ) conn.commit() conn.close()

def register_user(user: User): """Registra al usuario en la tabla usuarios (si no existe).""" conn = _connect() cur = conn.cursor() cur.execute( "INSERT OR IGNORE INTO usuarios (id_usuario, username, nombre, estado, fecha_registro, rol) " "VALUES (?, ?, ?, 'activo', datetime('now','localtime'), 'VIP')", (user.id, user.username or '', user.first_name) ) conn.commit() conn.close()

def save_payment_request(user_id, codes, amount, comprobante_file_id=None): """Guarda la solicitud de pago en la tabla pagos.""" period = ",".join(codes) conn = _connect() cur = conn.cursor() cur.execute( "INSERT INTO pagos (id_usuario, periodo, monto, comprobante, estado, fecha) " "VALUES (?, ?, ?, ?, 'pendiente', datetime('now','localtime'))", (user_id, period, amount, comprobante_file_id or '') ) conn.commit() conn.close()

