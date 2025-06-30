# helpers.py

import sqlite3
import calendar
from datetime import datetime
from telebot.types import User

from markups import MONTHS

# Ruta de la base de datos SQLite
db = 'bot.db'

# --- Funciones auxiliares de fechas y montos ---

def parse_code(code_str):
    """
    ⚙️ Parsea un código de pago que puede incluir año:
    - 'ene' → mes actual (año implícito)
    - '2025-feb' → febrero de 2025
    Devuelve (año, código_mes).
    """
    if '-' in code_str:
        year_str, month_code = code_str.split('-', 1)
        try:
            y = int(year_str)
        except ValueError:
            y = datetime.now().year
        return y, month_code
    return datetime.now().year, code_str

def days_in_month(code_str):
    """
    Calcula la cantidad de días del mes dado (con o sin año).
    """
    year, mcode = parse_code(code_str)
    m_idx = [c for c, _ in MONTHS].index(mcode) + 1
    return calendar.monthrange(year, m_idx)[1]

def calculate_total_days(codes):
    """
    🔢 Suma los días de todas las etiquetas de mes proporcionadas.
    """
    return sum(days_in_month(c) for c in codes)

def calculate_amount(total_days, price_per_day):
    """
    💰 Calcula el monto total a pagar según días y tarifa diaria.
    """
    return total_days * price_per_day

def calculate_expiration_date(codes):
    """
    📅 Devuelve la fecha de vencimiento (último día) del último periodo seleccionado.
    """
    # Parse y orden por año y mes
    parsed = []
    for c in codes:
        y, mcode = parse_code(c)
        midx = [cm for cm, _ in MONTHS].index(mcode) + 1
        parsed.append((y, midx))
    parsed.sort()
    last_year, last_month = parsed[-1]
    last_day = calendar.monthrange(last_year, last_month)[1]
    return datetime(last_year, last_month, last_day).strftime('%Y-%m-%d')

# --- Funciones de base de datos ---

def _conn():
    return sqlite3.connect(db)

def log_action(action):
    """
    📝 Registra una acción en la tabla 'log' con timestamp.
    """
    c = _conn().cursor()
    c.execute(
        "INSERT INTO log (accion, fecha) VALUES (?, datetime('now','localtime'))",
        (action,)
    )
    c.connection.commit()
    c.connection.close()

def register_user(user: User):
    """
    👤 Inserta al usuario en 'usuarios' si no existía:
    - id_usuario, username, nombre, estado='activo', fecha_registro
    """
    c = _conn().cursor()
    c.execute(
        "INSERT OR IGNORE INTO usuarios"
        " (id_usuario, username, nombre, estado, fecha_registro, rol)"
        " VALUES (?, ?, ?, 'activo', datetime('now','localtime'), 'VIP')",
        (user.id, user.username or '', user.first_name)
    )
    c.connection.commit()
    c.connection.close()

def save_payment_request(user_id, codes, amount, comprobante=None):
    """
    📥 Guarda una nueva solicitud en 'pagos':
    - id_usuario, periodo (lista de códigos), monto, comprobante opcional, estado='pendiente'
    """
    period = ",".join(codes)
    c = _conn().cursor()
    c.execute(
        "INSERT INTO pagos"
        " (id_usuario, periodo, monto, comprobante, estado, fecha)"
        " VALUES (?, ?, ?, ?, 'pendiente', datetime('now','localtime'))",
        (user_id, period, amount, comprobante or '')
    )
    c.connection.commit()
    c.connection.close()
