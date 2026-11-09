#!/bin/bash
# Ejecuta el job de Hadoop Streaming y la version secuencial, mide ambos
# tiempos y compara los resultados.
# Uso (desde el host):  docker compose exec -u hadoop hadoop bash run_job.sh
set -e
MATRICULA=125052501
INPUT=/data/input/ventas_${MATRICULA}.csv
OUTPUT=/data/output/resultado
cd /opt/mapreduce

# Hadoop falla si la carpeta de salida ya existe
rm -rf "$OUTPUT"

echo "===== Hadoop Streaming ====="
time hadoop jar $HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-*.jar \
    -input "$INPUT" \
    -output "$OUTPUT" \
    -mapper "python3 mapper.py" -reducer "python3 reducer.py" \
    -file mapper.py -file reducer.py

echo
echo "===== Secuencial (Python) ====="
time python3 secuencial.py "$INPUT" > /data/output/secuencial.tsv

echo
echo "===== Comparacion ====="
if diff -q "$OUTPUT/part-00000" /data/output/secuencial.tsv; then
    echo "OK: resultados identicos ($(wc -l < /data/output/secuencial.tsv) filas)"
else
    echo "DIFERENCIAS entre Hadoop y secuencial"
    exit 1
fi
