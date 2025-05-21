import sqlite3
import pandas as pd


DB_PATH = "db/cotizaciones.db"

def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def create_tables():
    with get_connection() as con:
        cur = con.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS cotizaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha_inicio TEXT,
                nombre_cliente TEXT,
                correo TEXT,
                telefono TEXT NOT NULL,
                auto TEXT,
                observacion TEXT,
                fecha_ultimo_contacto TEXT,
                visita_programada TEXT,
                estado TEXT,
                whatsapp_link TEXT
            )
        """)
        con.commit()

def agregar_columna_link_auto():
    with get_connection() as con:
        cur = con.cursor()
        cur.execute("PRAGMA table_info(cotizaciones)")
        columnas = [col[1] for col in cur.fetchall()]
        if "link_auto" not in columnas:
            cur.execute("ALTER TABLE cotizaciones ADD COLUMN link_auto TEXT")
            con.commit()

def crear_tabla_mensajes():
    with get_connection() as con:
        cur = con.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS mensajes_whatsapp (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                mensaje TEXT NOT NULL,
                descripcion TEXT 
            )
        """)
        con.commit()      

def insertar_mensaje(nombre, mensaje, descripcion=None):
    with get_connection() as con:
        cur = con.cursor()
        cur.execute("""
            INSERT INTO mensajes_whatsapp (nombre, mensaje, descripcion)
            VALUES (?, ?, ?)
        """, (nombre, mensaje, descripcion))
        con.commit() 

def obtener_mensajes_whatsapp():
    with get_connection() as con:
        cur = con.cursor()
        cur.execute("SELECT id, nombre, mensaje, descripcion FROM mensajes_whatsapp ORDER BY id ASC")
        return cur.fetchall()  # [(id, nombre, mensaje, descripcion), ...]
    
def actualizar_mensaje(id_, nombre, mensaje, descripcion):
    with get_connection() as con:
        cur = con.cursor()
        cur.execute("""
            UPDATE mensajes_whatsapp
            SET nombre = ?, mensaje = ?, descripcion = ?
            WHERE id = ?
        """, (nombre, mensaje, descripcion, id_))
        con.commit()

def eliminar_mensaje(id_):
    with get_connection() as con:
        cur = con.cursor()
        cur.execute("DELETE FROM mensajes_whatsapp WHERE id = ?", (id_,))
        con.commit()

    
def insertar_cotizacion(data):
    with get_connection() as con:
        cur = con.cursor()
        cur.execute("""
            INSERT INTO cotizaciones (
                fecha_inicio, nombre_cliente, correo, telefono, auto,
                observacion, fecha_ultimo_contacto, visita_programada,
                estado, whatsapp_link , link_auto
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, data)
        con.commit()

def obtener_cotizaciones(filtros, limite=200):
    with get_connection() as con:
        cur = con.cursor()
        query = "SELECT * FROM cotizaciones WHERE 1=1"
        parametros = []

        if filtros.get("nombre"):
            query += " AND nombre_cliente LIKE ?"
            parametros.append(f"%{filtros['nombre']}%")
        if filtros.get("telefono"):
            query += " AND telefono LIKE ?"
            parametros.append(f"%{filtros['telefono']}%")
        if filtros.get("auto"):
            query += " AND auto LIKE ?"
            parametros.append(f"%{filtros['auto']}%")

        query += " ORDER BY fecha_inicio DESC LIMIT ?"
        parametros.append(limite)

        cur.execute(query, parametros)
        columnas = [col[0] for col in cur.description]
        return pd.DataFrame(cur.fetchall(), columns=columnas)


def actualizar_cotizacion(id_, data):
    with get_connection() as con:
        cur = con.cursor()
        cur.execute("""
            UPDATE cotizaciones SET
                fecha_inicio = ?, nombre_cliente = ?, correo = ?, telefono = ?,
                auto = ?, observacion = ?, fecha_ultimo_contacto = ?,
                visita_programada = ?, estado = ?, whatsapp_link = ?, link_auto = ?
            WHERE id = ?
        """, data + (id_,))
        con.commit()

def eliminar_cotizacion(id_):
    with get_connection() as con:
        cur = con.cursor()
        cur.execute("DELETE FROM cotizaciones WHERE id = ?", (id_,))
        con.commit()
        