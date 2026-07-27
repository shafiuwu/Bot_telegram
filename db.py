import sqlite3


def crear_tabla():
    conexion = sqlite3.connect("recordatorios.db")
    cursor = conexion.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recordatorios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            texto TEXT NOT NULL,
            fecha_hora TEXT NOT NULL,
            enviado INTEGER DEFAULT 0
        )
    """)

    conexion.commit()
    conexion.close()


def migrar_frecuencia():
    conexion = sqlite3.connect("recordatorios.db")
    cursor = conexion.cursor()
    try:
        cursor.execute("ALTER TABLE recordatorios ADD COLUMN frecuencia TEXT DEFAULT 'unica'")
        conexion.commit()
    except sqlite3.OperationalError:
        pass
    conexion.close()


def agregar_recordatorio(chat_id, texto, fecha_hora, frecuencia):
    conexion = sqlite3.connect("recordatorios.db")
    cursor = conexion.cursor()

    cursor.execute(
        "INSERT INTO recordatorios (chat_id, texto, fecha_hora, frecuencia) VALUES (?, ?, ?, ?)",
        (chat_id, texto, fecha_hora, frecuencia)
    )

    conexion.commit()
    ultimo_id = cursor.lastrowid
    conexion.close()
    return ultimo_id


def obtener_pendientes():
    conexion = sqlite3.connect("recordatorios.db")
    cursor = conexion.cursor()

    cursor.execute(
        "SELECT id, chat_id, texto, fecha_hora, frecuencia FROM recordatorios WHERE enviado = 0"
    )
    filas = cursor.fetchall()

    conexion.close()
    return filas


def marcar_enviado(id_recordatorio):
    conexion = sqlite3.connect("recordatorios.db")
    cursor = conexion.cursor()

    cursor.execute("UPDATE recordatorios SET enviado = 1 WHERE id = ?", (id_recordatorio,))

    conexion.commit()
    conexion.close()


def cancelar_recordatorio(id_recordatorio):
    conexion = sqlite3.connect("recordatorios.db")
    cursor = conexion.cursor()

    cursor.execute("UPDATE recordatorios SET enviado = 1 WHERE id = ?", (id_recordatorio,))
    conexion.commit()

    filas_afectadas = cursor.rowcount
    conexion.close()
    return filas_afectadas


if __name__ == "__main__":
    crear_tabla()
    migrar_frecuencia()
    print("Tabla lista.")