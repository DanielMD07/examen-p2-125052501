#!/usr/bin/env python3
"""Version secuencial (sin Hadoop) de la misma pregunta:
ingreso total por categoria y mes, leyendo el CSV linea a linea.

Uso: python3 secuencial.py /data/input/ventas_125052501.csv > salida.tsv
La salida tiene el mismo formato que la del reducer para poder hacer diff.
"""
import sys
from collections import defaultdict


def main():
    ruta = sys.argv[1] if len(sys.argv) > 1 else "/data/input/ventas_125052501.csv"
    totales = defaultdict(int)  # (categoria, mes) -> centavos
    malformadas = 0

    with open(ruta, encoding="utf-8") as f:
        next(f)  # encabezado
        for linea in f:
            campos = linea.rstrip("\r\n").split(",")
            try:
                if len(campos) != 8:
                    raise ValueError
                mes = campos[1][:7]
                categoria = campos[3].strip()
                totales[(categoria, mes)] += int(campos[5]) * round(float(campos[6]) * 100)
            except (ValueError, IndexError):
                malformadas += 1

    # Mismo orden que la salida de Hadoop (ordenada por la clave "categoria|mes")
    for categoria, mes in sorted(totales, key=lambda k: f"{k[0]}|{k[1]}"):
        c = totales[(categoria, mes)]
        print(f"{categoria}\t{mes}\t{c // 100}.{c % 100:02d}")

    sys.stderr.write(f"Lineas mal formadas: {malformadas}\n")


if __name__ == "__main__":
    main()
