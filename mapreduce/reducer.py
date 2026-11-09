#!/usr/bin/env python3
"""Reducer - suma los centavos de cada clave <categoria>|<YYYY-MM>.

Hadoop entrega las claves ya ordenadas, asi que basta con acumular
mientras la clave no cambie.
Salida: <categoria> \t <YYYY-MM> \t <ingreso_total con 2 decimales>
"""
import sys


def emitir(clave, total_centavos):
    categoria, mes = clave.split("|")
    print(f"{categoria}\t{mes}\t{total_centavos // 100}.{total_centavos % 100:02d}")


def main():
    clave_actual = None
    total = 0

    for linea in sys.stdin:
        try:
            clave, valor = linea.rstrip("\n").split("\t")
            valor = int(valor)
        except ValueError:
            sys.stderr.write("reporter:counter:DataMart,ParesInvalidos,1\n")
            continue

        if clave != clave_actual:
            if clave_actual is not None:
                emitir(clave_actual, total)
            clave_actual = clave
            total = 0
        total += valor

    if clave_actual is not None:
        emitir(clave_actual, total)


if __name__ == "__main__":
    main()
