#!/bin/bash
# Recorre las evidencias del examen una por una para tomar las capturas.
#
# Uso (desde la raiz del repo, con el ambiente levantado):
#     bash scripts/demo_capturas.sh
#
# En cada paso: toma la captura con la tecla Impr Pant (Print Screen) y luego
# presiona Enter. El script mueve la captura mas reciente de
# ~/Pictures/Screenshots a evidencias/<nombre>.png
#
# Con SIN_PAUSA=1 corre todo de corrido (para probar que no falle nada).

cd "$(dirname "$0")/.." || exit 1
CAPTURAS="$HOME/Pictures/Screenshots"
API="http://localhost:${API_PORT:-8000}"
JSON='Content-Type: application/json'

# Colores
AZUL='\e[1;34m'; VERDE='\e[1;32m'; AMARILLO='\e[1;33m'; NORMAL='\e[0m'

titulo() {
    clear
    MARCA=$(mktemp)  # para saber que capturas son nuevas
    echo -e "${AZUL}==================================================================${NORMAL}"
    echo -e "${AZUL} Examen P2 - Matricula 125052501 - $1${NORMAL}"
    echo -e "${AZUL}==================================================================${NORMAL}"
    echo
}

# Muestra el comando como si se hubiera tecleado y lo ejecuta
cmd() {
    echo -e "${VERDE}\$ $*${NORMAL}"
    eval "$@"
    echo
}

guardar() {
    local nombre="$1"
    if [ -n "$SIN_PAUSA" ]; then
        echo -e "${AMARILLO}[SIN_PAUSA] aqui se guardaria evidencias/$nombre.png${NORMAL}"
        rm -f "$MARCA"
        return
    fi
    echo -e "${AMARILLO}>> Toma la captura (Impr Pant) y presiona Enter...${NORMAL}"
    read -r
    local nueva
    nueva=$(find "$CAPTURAS" -maxdepth 1 -name '*.png' -newer "$MARCA" -printf '%T@ %p\n' 2>/dev/null \
            | sort -n | tail -1 | cut -d' ' -f2-)
    if [ -n "$nueva" ]; then
        mv "$nueva" "evidencias/$nombre.png"
        echo -e "${VERDE}Guardada: evidencias/$nombre.png${NORMAL}"
    else
        echo -e "${AMARILLO}No encontre captura nueva en $CAPTURAS (puedes copiarla despues como evidencias/$nombre.png)${NORMAL}"
    fi
    rm -f "$MARCA"
    sleep 1
}

# 1. Servicios arriba
titulo "A2. Servicios del docker-compose"
cmd docker compose ps
cmd 'docker volume ls | grep examen-p2'
cmd 'docker network ls | grep datamart'
guardar 01_compose_ps

# 2. Hadoop instalado
titulo "A1. Java y Hadoop dentro del contenedor"
cmd docker compose exec hadoop java -version
cmd 'docker compose exec hadoop hadoop version | head -4'
cmd "docker compose exec hadoop bash -c 'echo JAVA_HOME=\$JAVA_HOME; echo HADOOP_HOME=\$HADOOP_HOME; echo PATH=\$PATH'"
guardar 02_hadoop_version

# 3. SSH localhost
titulo "B. ssh localhost sin contrasena (dentro de hadoop)"
cmd "docker compose exec hadoop grep -E '^(PasswordAuthentication|PermitRootLogin)' /etc/ssh/sshd_config"
cmd 'docker compose exec -u hadoop hadoop ls -l /home/hadoop/.ssh'
cmd "docker compose exec -u hadoop hadoop ssh -o BatchMode=yes localhost 'echo Conectado a \$(hostname) como \$(whoami); hadoop version | head -1'"
guardar 03_ssh_localhost

# 4. SSH api -> hadoop
titulo "B. ssh desde el contenedor api hacia hadoop (por nombre de servicio)"
cmd docker compose exec api cat /etc/ssh/ssh_config.d/hadoop.conf
cmd "docker compose exec api ssh -o BatchMode=yes hadoop 'echo Conectado a \$(hostname) como \$(whoami); hadoop version | head -1'"
guardar 04_ssh_api_a_hadoop

# 5. Job MapReduce + comparativa
titulo "C1/C2. Job Hadoop Streaming + secuencial (tarda ~20 s)"
cmd 'docker compose exec -u hadoop hadoop bash run_job.sh | grep -E "number of splits|Map input records=5|Map output records=5|completed successfully|=====|^(real|user|sys)\s|OK:|DIFERENCIAS"'
guardar 05_job_y_tiempos

# 6. Salida del job
titulo "C1. Salida del job (part-00000)"
cmd 'ls -l output/resultado/'
cmd 'head -15 output/resultado/part-00000'
cmd 'wc -l output/resultado/part-00000'
guardar 06_salida_job

# 7. Carga + GET
titulo "D. Carga a MySQL y consultas GET"
cmd docker compose exec api python scripts/cargar_resultados.py
cmd "curl -s $API/resultados | jq length"
cmd "curl -s $API/resultados | jq -c '.[0:3][]'"
cmd "curl -s $API/resultados/Electronica | jq -c '.[]'"
guardar 07_carga_y_get

# 8. Escritura
titulo "D. Endpoints de escritura (POST, PUT, DELETE)"
echo -e "${VERDE}\$ curl -s -X POST $API/resultados -H '$JSON' -d '{\"categoria\":\"Prueba\",\"mes\":\"2026-01\",\"ingreso\":123.45}'${NORMAL}"
NUEVO=$(curl -s -X POST "$API/resultados" -H "$JSON" -d '{"categoria":"Prueba","mes":"2026-01","ingreso":123.45}')
echo "$NUEVO"; echo
ID=$(echo "$NUEVO" | jq -r .id)
cmd "curl -s -X PUT $API/resultados/$ID -H '$JSON' -d '{\"ingreso\":999.99}'"
cmd "curl -s $API/resultados/Prueba"
cmd "curl -s -X DELETE $API/resultados/$ID"
cmd "curl -s $API/resultados/Prueba"
guardar 08_post_put_delete

# 9. Persistencia
titulo "D. Persistencia: docker compose down / up"
cmd "curl -s $API/resultados | jq length"
cmd 'docker compose down 2>&1 | grep -v Removing'
cmd 'docker volume ls | grep db_data'
cmd 'docker compose up -d 2>&1 | grep -E "Started|Healthy"'
echo -e "${VERDE}\$ curl -s $API/resultados | jq length${NORMAL}"
for i in $(seq 30); do curl -s "$API/resultados" >/dev/null 2>&1 && break; sleep 1; done
curl -s "$API/resultados" | jq length; echo
guardar 09_persistencia

clear
echo -e "${VERDE}Listo. Capturas en evidencias/:${NORMAL}"
ls -1 evidencias/*.png 2>/dev/null
