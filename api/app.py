"""API DataMart - CRUD (adaptado del CRUD de contactos en Flask) sobre los
resultados del job MapReduce: ingreso total por categoria y mes.

GET    /resultados                      todos los registros
GET    /resultados/<categoria>          filtro por categoria (opcional ?mes=YYYY-MM)
POST   /resultados                      crea un registro
PUT    /resultados/<id>                 actualiza un registro
DELETE /resultados/<id>                 elimina un registro
"""
import re

import pymysql
from flask import Flask, jsonify, request

from db import TABLA, crear_tabla, get_connection

app = Flask(__name__)
app.json.sort_keys = False

MES_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def a_json(fila):
    fila["ingreso"] = float(fila["ingreso"])
    return fila


def validar(datos, parcial=False):
    """Regresa (campos_validos, error)."""
    campos = {}
    if "categoria" in datos or not parcial:
        categoria = str(datos.get("categoria", "")).strip()
        if not categoria:
            return None, "categoria es obligatoria"
        campos["categoria"] = categoria
    if "mes" in datos or not parcial:
        mes = str(datos.get("mes", ""))
        if not MES_RE.match(mes):
            return None, "mes debe tener formato YYYY-MM"
        campos["mes"] = mes
    if "ingreso" in datos or not parcial:
        try:
            campos["ingreso"] = round(float(datos.get("ingreso")), 2)
        except (TypeError, ValueError):
            return None, "ingreso debe ser numerico"
    if not campos:
        return None, "no hay campos para actualizar"
    return campos, None


@app.get("/")
def index():
    return jsonify(servicio="API DataMart", pregunta="Ingreso total por categoria y mes",
                   endpoints=["/resultados", "/resultados/<categoria>?mes=YYYY-MM"])


@app.get("/resultados")
def listar():
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(f"SELECT * FROM {TABLA} ORDER BY categoria, mes")
        filas = cur.fetchall()
    conn.close()
    return jsonify([a_json(f) for f in filas])


@app.get("/resultados/<categoria>")
def por_categoria(categoria):
    sql = f"SELECT * FROM {TABLA} WHERE categoria = %s"
    params = [categoria]
    mes = request.args.get("mes")
    if mes:
        sql += " AND mes = %s"
        params.append(mes)
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(sql + " ORDER BY mes", params)
        filas = cur.fetchall()
    conn.close()
    if not filas:
        return jsonify(error=f"sin resultados para '{categoria}'"), 404
    return jsonify([a_json(f) for f in filas])


@app.post("/resultados")
def crear():
    campos, error = validar(request.get_json(silent=True) or {})
    if error:
        return jsonify(error=error), 400
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(f"INSERT INTO {TABLA} (categoria, mes, ingreso) VALUES (%s, %s, %s)",
                        (campos["categoria"], campos["mes"], campos["ingreso"]))
            nuevo_id = cur.lastrowid
        conn.commit()
    except pymysql.err.IntegrityError:
        return jsonify(error="ya existe un registro para esa categoria y mes"), 409
    finally:
        conn.close()
    return jsonify(id=nuevo_id, **campos), 201


@app.put("/resultados/<int:id>")
def actualizar(id):
    campos, error = validar(request.get_json(silent=True) or {}, parcial=True)
    if error:
        return jsonify(error=error), 400
    sets = ", ".join(f"{c} = %s" for c in campos)
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(f"UPDATE {TABLA} SET {sets} WHERE id = %s", (*campos.values(), id))
            cur.execute(f"SELECT * FROM {TABLA} WHERE id = %s", (id,))
            fila = cur.fetchone()
        conn.commit()
    except pymysql.err.IntegrityError:
        return jsonify(error="ya existe un registro para esa categoria y mes"), 409
    finally:
        conn.close()
    if fila is None:
        return jsonify(error="registro no encontrado"), 404
    return jsonify(a_json(fila))


@app.delete("/resultados/<int:id>")
def eliminar(id):
    conn = get_connection()
    with conn.cursor() as cur:
        borrados = cur.execute(f"DELETE FROM {TABLA} WHERE id = %s", (id,))
    conn.commit()
    conn.close()
    if not borrados:
        return jsonify(error="registro no encontrado"), 404
    return jsonify(mensaje=f"registro {id} eliminado")


if __name__ == "__main__":
    crear_tabla()
    app.run(host="0.0.0.0", port=8000)
