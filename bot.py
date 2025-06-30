# bot.py

import config
from database import init_db
from scheduler import start_scheduler

# Importa los módulos que registran automáticamente todos los handlers
import user_handlers
import admin_handlers

if __name__ == "__main__":
    # 1. Iniciar o actualizar la base de datos
    init_db()

    # 2. Arrancar el scheduler de recordatorios (3 días y horas antes)
    start_scheduler()

    # 3. Arrancar el bot (los handlers ya están cargados)
    print("✅ Bot en ejecución...")
    user_handlers.user_bot.infinity_polling()
