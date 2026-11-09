#!/usr/bin/env python3
"""Mapper - Ingreso total (cantidad * precio_unitario) por categoria y mes.

Entrada (CSV): id,fecha_hora,tienda,categoria,producto,cantidad,precio_unitario,metodo_pago
Salida:        <categoria>|<YYYY-MM> \t <ingreso en centavos>

El ingreso se emite en centavos (entero) para que la suma sea exacta y
coincida al centavo con el script secuencial (sin errores de punto flotante).
"""
import sys

NUM_CAMPOS = 8


def main():
    for linea in sys.stdin:
        campos = linea.rstrip("\r\n").split(",")

        # Encabezado: se ignora
        if campos[0] == "id":
            continue

        try:
            if len(campos) != NUM_CAMPOS:
                raise ValueError("numero de campos incorrecto")
            fecha_hora = campos[1]
            categoria = campos[3].strip()
            cantidad = int(campos[5])
            centavos = round(float(campos[6]) * 100)
            mes = fecha_hora[:7]  # "2025-03-14 10:22:01" -> "2025-03"
            if not categoria or len(mes) != 7 or mes[4] != "-":
                raise ValueError("categoria o fecha invalida")
        except (ValueError, IndexError):
            # Linea mal formada: se cuenta y se descarta, el job sigue
            sys.stderr.write("reporter:counter:DataMart,LineasMalFormadas,1\n")
            continue

        print(f"{categoria}|{mes}\t{cantidad * centavos}")


if __name__ == "__main__":
    main()
