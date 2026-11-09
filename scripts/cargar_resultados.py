#!/usr/bin/env python3
"""Lee la salida del job MapReduce (part-00000) y la inserta en MySQL.

Uso (desde el host):
    docker compose exec api python scripts/cargar_resultados.py

Cada linea de entrada: <categoria> \t <YYYY-MM> \t <ingreso>
Es idempotente: si se corre dos veces, actualiza en lugar de duplicar.
"""
import glob
import sys

sys.path.insert(0, "/app")  # para importar db.py de la api
from db import TABLA, crear_tabla, get_connection  # noqa: E402

DIR_SALIDA = sys.argv[1] if len(sys.argv) > 1 else "/data/output/resultado"


def main():
    archivos = sorted(glob.glob(f"{DIR_SALIDA}/part-*"))
    if not archivos:
        sys.exit(f"No hay archivos part-* en {DIR_SALIDA}. Corre primero el job.")

    registros = []
    for archivo in archivos:
        with open(archivo, encoding="utf-8") as f:
            for linea in f:
                partes = linea.rstrip("\n").split("\t")
                if len(partes) != 3:
                    continue
                categoria, mes, ingreso = partes
                registros.append((categoria, mes, ingreso))

    crear_tabla()
    conn = get_connection()
    with conn.cursor() as cur:
        cur.executemany(
            f"""INSERT INTO {TABLA} (categoria, mes, ingreso) VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE ingreso = VALUES(ingreso)""",
            registros,
        )
        cur.execute(f"SELECT COUNT(*) AS n FROM {TABLA}")
        total = cur.fetchone()["n"]
    conn.commit()
    conn.close()
    print(f"Cargados {len(registros)} registros desde {len(archivos)} archivo(s). "
          f"Filas en {TABLA}: {total}")


if __name__ == "__main__":
    main()
