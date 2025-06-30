import sqlite3

def init_db():
    conn = sqlite3.connect("bot.db")
    cur = conn.cursor()

    # Tabla de usuarios
    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id_usuario INTEGER PRIMARY KEY,
            username TEXT,
            nombre TEXT,
            estado TEXT,
            fecha_registro TEXT,
            rol TEXT,
            fecha_vencimiento TEXT
        );
    """)

    # Tabla de pagos
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pagos (
            id_pago INTEGER PRIMARY KEY AUTOINCREMENT,
            id_usuario INTEGER,
            periodo TEXT,
            monto REAL,
            comprobante TEXT,
            estado TEXT,
            fecha TEXT,
            FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
        );
    """)

    # Tabla de logs (auditoría)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS log (
            id_log INTEGER PRIMARY KEY AUTOINCREMENT,
            accion TEXT,
            fecha TEXT
        );
    """)

    conn.commit()
    conn.close()
    print("✅ Base de datos creada correctamente.")

if __name__ == "__main__":
    init_db()
