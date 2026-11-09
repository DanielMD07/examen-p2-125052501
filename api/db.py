import os

import pymysql

TABLA = "ingresos_categoria_mes"

DDL = f"""
CREATE TABLE IF NOT EXISTS {TABLA} (
    id        INT AUTO_INCREMENT PRIMARY KEY,
    categoria VARCHAR(50)    NOT NULL,
    mes       CHAR(7)        NOT NULL,   -- YYYY-MM
    ingreso   DECIMAL(16, 2) NOT NULL,
    UNIQUE KEY uq_categoria_mes (categoria, mes)
)
"""


def get_connection():
    # Se conecta al servicio "db" por su nombre dentro de la red del compose
    return pymysql.connect(
        host=os.getenv("DB_HOST", "db"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE"),
        cursorclass=pymysql.cursors.DictCursor,
    )


def crear_tabla():
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(DDL)
    conn.commit()
    conn.close()
