# Examen Segundo Parcial — Pipeline de datos contenerizado

**Materia:** Manejo Masivo de Datos (Big Data)
**Alumno:** Daniel Efrén Malagón De Santiago
**Matrícula:** 125052501 (último dígito **1**)
**Pregunta de negocio asignada:** *Ingreso total (`cantidad × precio_unitario`) por categoría y mes.*

## Arquitectura

```
 ./data/ventas_125052501.csv  (ro)        ./output (rw)                 volumen db_data
            │                                 │                               │
            ▼                                 ▼                               ▼
   ┌──────────────────┐   part-00000   ┌──────────────┐   PyMySQL     ┌──────────────┐
   │ hadoop           │ ─────────────► │ api (Flask)  │ ────────────► │ db (MySQL 8) │
   │ Debian 12, JDK17 │ ◄───── ssh ─── │ :8000        │   host "db"   │              │
   │ Hadoop 3.3.6     │                └──────────────┘               └──────────────┘
   │ sshd (llaves)    │        todos en la red  datamart-net
   └──────────────────┘
```

| Servicio | Imagen | Función |
|---|---|---|
| `hadoop` | `hadoop/Dockerfile` (Debian 12 + OpenJDK 17 + Python 3 + Hadoop 3.3.6 standalone + OpenSSH) | Ejecuta el job MapReduce y el script secuencial |
| `db` | `mysql:8.4` | Guarda los resultados; volumen nombrado `db_data` |
| `api` | `api/Dockerfile` (Flask) | CRUD sobre la tabla `ingresos_categoria_mes`; `depends_on: db (service_healthy)` |

Volúmenes nombrados: `db_data` (persistencia de MySQL) y `ssh_keys` (par de llaves que genera `hadoop` al arrancar y que `api` monta en solo lectura).

## Cómo reproducir

```bash
# 0. Credenciales (el .env NO se sube al repo)
cp .env.example .env          # y cambia las contraseñas

# 1. Dataset (no se sube: está en .gitignore)
cd data && python3 ../scripts/generar_dataset.py 125052501 && cd ..

# 2. Levantar todo con un solo comando
#    (opcional: si hadoop/hadoop-3.3.6.tar.gz existe se usa ese; si no, se descarga de Apache)
docker compose up -d --build

# 3. Correr el job de Hadoop + el secuencial + comparación de resultados
docker compose exec -u hadoop hadoop bash run_job.sh

# 4. Cargar la salida del job en MySQL
docker compose exec api python scripts/cargar_resultados.py

# 5. Consultar la API
curl http://localhost:8000/resultados
curl http://localhost:8000/resultados/Electronica
curl "http://localhost:8000/resultados/Electronica?mes=2025-03"
```

### Verificaciones de la Parte A y B

```bash
docker compose exec hadoop hadoop version                      # A1
docker compose exec -u hadoop hadoop ssh localhost hostname    # B: ssh localhost sin contraseña
docker compose exec api ssh hadoop 'hostname && whoami'        # B: api -> hadoop por nombre de servicio
```

### Endpoints de la API

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/resultados` | Todos los registros |
| GET | `/resultados/<categoria>` | Filtro por categoría (opcional `?mes=YYYY-MM`) |
| POST | `/resultados` | Crea un registro `{"categoria","mes","ingreso"}` |
| PUT | `/resultados/<id>` | Actualiza uno o más campos |
| DELETE | `/resultados/<id>` | Elimina un registro |

```bash
curl -X POST localhost:8000/resultados -H 'Content-Type: application/json' \
     -d '{"categoria":"Prueba","mes":"2026-01","ingreso":123.45}'
# <id> = el id que regresó el POST
curl -X PUT localhost:8000/resultados/<id> -H 'Content-Type: application/json' -d '{"ingreso":999.99}'
curl -X DELETE localhost:8000/resultados/<id>
```

Evidencias: `evidencias/06_carga_y_api_get.txt` (carga + GET) y `evidencias/07_api_escritura.txt` (POST 201, duplicado 409, validación 400, PUT, DELETE).

### Persistencia

```bash
docker compose down        # borra contenedores y red, NO el volumen db_data
docker compose up -d
curl localhost:8000/resultados    # los datos siguen ahí
```

Resultado real (`evidencias/08_persistencia.txt`): 120 registros antes del `down`, el volumen `examen-p2-125052501_db_data` sigue en `docker volume ls`, y hay 120 registros después del `up`. Con `docker compose down -v` el volumen se elimina, la tabla queda vacía (0 registros) y se recupera volviendo a correr `cargar_resultados.py`.

### Evidencias

| Archivo | Qué demuestra |
|---|---|
| `evidencias/01_compose_up.txt` | `docker compose up -d --build` levanta los 3 servicios; `db` healthy |
| `evidencias/02_hadoop_version.txt` | `java -version`, `hadoop version`, `JAVA_HOME`, `HADOOP_HOME`, `PATH` |
| `evidencias/03_ssh.txt` | `ssh localhost` y `api → ssh hadoop` sin contraseña (`BatchMode=yes`); `PasswordAuthentication no` |
| `evidencias/04_job_y_comparativa.log` | Log completo del job, tiempos y `diff` contra el secuencial |
| `evidencias/05_lineas_malformadas.txt` | El job no se cae con líneas dañadas |
| `evidencias/06_carga_y_api_get.txt` | Carga a MySQL y respuestas de los GET |
| `evidencias/07_api_escritura.txt` | POST / PUT / DELETE |
| `evidencias/08_persistencia.txt` | `down` / `up` y `down -v` |

## Cómo funciona el SSH (Parte B)

- El usuario `hadoop` se crea con `passwd -l` (cuenta sin contraseña) y `sshd_config` tiene `PasswordAuthentication no` y `PermitRootLogin no`: **solo se entra con llave**, y no hay ninguna contraseña en el Dockerfile.
- Al arrancar, `hadoop/entrypoint.sh` corre `ssh-keygen -t rsa -P ''` (solo la primera vez) dentro del volumen `ssh_keys`, copia la llave pública a `~hadoop/.ssh/authorized_keys` y levanta `sshd`. Las llaves de host también viven en el volumen, para que no cambien si el contenedor se recrea.
- `api` monta el mismo volumen en solo lectura (`/keys`) y en `/etc/ssh/ssh_config.d/hadoop.conf` tiene `User hadoop` + `IdentityFile /keys/id_rsa`, así que `ssh hadoop` resuelve el nombre del servicio por el DNS de la red `datamart-net`.

## Guía rápida para la defensa (Parte F)

**Cambiar el puerto de la API:** editar `API_PORT` en `.env` (o `API_PORT=9000 docker compose up -d api`). El compose publica `"${API_PORT:-8000}:8000"`: el número de la izquierda es el puerto del host, el de la derecha es donde escucha Flask dentro del contenedor.

**Cambiar la agregación** (ejemplo: promedio por registro en lugar de suma): el mapper ya emite un valor por registro, así que solo cambia el reducer: llevar también un contador `n += 1` y emitir `total / n`. Para filtrar por mes, en el mapper agregar `if mes != "2025-03": continue` antes del `print`. Después: `docker compose exec -u hadoop hadoop bash run_job.sh` (borra la salida anterior; Hadoop falla si la carpeta de salida ya existe). Como `./mapreduce` está montado como volumen, no hace falta reconstruir la imagen.

**Borrar el volumen y recargar:**
```bash
docker compose down -v
docker compose up -d
docker compose exec api python scripts/cargar_resultados.py
```

**Diagnóstico de errores comunes:**
- `Output directory ... already exists` → borrar `output/resultado` (lo hace `run_job.sh`).
- La API no conecta a la base → `docker compose ps` (¿`db` está *healthy*?) y `docker compose logs db`.
- `REMOTE HOST IDENTIFICATION HAS CHANGED` en `api` → las llaves de host cambiaron (por un `down -v`); `docker compose exec api ssh-keygen -R hadoop`.
- Errores del mapper en Hadoop → probarlo sin Hadoop: `head -1000 data/ventas_125052501.csv | python3 mapreduce/mapper.py | sort | python3 mapreduce/reducer.py`.

## Diseño del job MapReduce

- **mapper.py**: lee cada línea, ignora el encabezado (`id,...`), valida que tenga 8 campos y que cantidad/precio sean numéricos. Las líneas mal formadas no truncan el job: se descartan y se cuentan con el contador de Hadoop `DataMart:LineasMalFormadas`. Emite `categoria|YYYY-MM \t ingreso_en_centavos`.
- **reducer.py**: recibe las claves ordenadas y suma mientras la clave no cambie. Emite `categoria \t mes \t ingreso`.
- El ingreso se maneja en **centavos enteros** para que la suma sea exacta y el resultado de Hadoop sea idéntico al del script secuencial (con `float` aparecerían diferencias de redondeo según el orden de las sumas).
- **secuencial.py**: misma lógica en un solo proceso, leyendo línea a línea con un `dict`.

## Resultados y comparativa (Parte C2)

Dataset: `ventas_125052501.csv`, 5,000,000 registros + encabezado, 336 MB. Máquina: 16 núcleos, Hadoop 3.3.6 en modo standalone (`LocalJobRunner`).

| Método | `real` | `user` | `sys` |
|---|---|---|---|
| Hadoop Streaming (`mapper.py` + `reducer.py`) | **12.21 s** | 19.78 s | 0.99 s |
| Secuencial (`secuencial.py`, línea a línea) | **3.36 s** | 3.32 s | 0.03 s |

- Contadores del job: `number of splits: 11`, `Map input records=5000001`, `Map output records=5000000` (se descartó el encabezado), `Reduce output records=120` (10 categorías × 12 meses).
- `diff` entre `output/resultado/part-00000` y `output/secuencial.tsv`: **resultados idénticos (120 filas)**. Log completo en `evidencias/04_job_y_comparativa.log`.
- Prueba de robustez: con un archivo con 4 líneas dañadas (pocos campos, cantidad no numérica, línea vacía) el job termina bien y reporta `DataMart: LineasMalFormadas=4` (`evidencias/05_lineas_malformadas.txt`).

Fragmento de la salida del job:

```
Abarrotes	2025-01	346079563.69
Abarrotes	2025-02	317343416.45
Abarrotes	2025-03	343628131.91
...
```

**¿Por qué el secuencial fue más rápido?** El script secuencial fue ~3.6 veces más rápido porque hace una sola pasada sobre el archivo en un único proceso y acumula en memoria un diccionario de apenas 120 claves. Hadoop, en cambio, paga un costo fijo que no depende del tamaño de los datos: arrancar la JVM, calcular los 11 splits, lanzar un intérprete de Python por cada tarea map y comunicarse con él por tuberías (stdin/stdout, convirtiendo todo a texto), escribir los 5 millones de pares intermedios a disco, ordenarlos en la fase de *shuffle & sort* y volver a leerlos en el reducer. En modo standalone todo eso ocurre en una sola máquina, sin HDFS ni nodos adicionales que repartan el trabajo, así que no hay paralelismo que compense el overhead: 336 MB caben de sobra en la memoria y el disco de una sola computadora. Hadoop solo empezaría a ganar con datos mucho más grandes (decenas o cientos de GB) distribuidos en un clúster real.

## Parte E. Teoría

**1. Standalone vs pseudo-distribuido vs totalmente distribuido.**
En *standalone* (modo local) Hadoop corre como un solo proceso Java, sin daemons, y lee/escribe directamente del sistema de archivos local; sirve para desarrollar y depurar. En *pseudo-distribuido* todos los daemons (NameNode, DataNode, ResourceManager, NodeManager) corren en una sola máquina, cada uno en su propia JVM, comunicándose por red local (por eso se necesita `ssh localhost` sin contraseña). En *totalmente distribuido* los daemons se reparten en varias máquinas de un clúster. HDFS se usa en los modos pseudo-distribuido y totalmente distribuido; en standalone no.

**2. ¿Por qué el dataset se monta como volumen y no con `COPY`?**
(a) Con `COPY` los ~400 MB quedan dentro de una capa de la imagen: la imagen pesa más, el build es más lento y cada cambio del CSV invalida la caché. (b) El dataset es distinto por alumno y cambia; la imagen debe ser genérica y reutilizable, y los datos se inyectan al ejecutar. (c) El CSV no debe ir al repositorio ni a un registry (es dato, no código); con `:ro` además se garantiza que el contenedor no lo modifique.

**3. `docker compose down` vs `docker compose down -v`.**
`docker compose down` detiene y elimina los contenedores y la red, pero los volúmenes nombrados (`db_data`) se conservan; al volver a levantar, MySQL encuentra sus datos. `docker compose down -v` además elimina los volúmenes nombrados declarados en el compose, así que la base de datos se pierde y MySQL se inicializa vacío en el siguiente `up` (hay que volver a correr `cargar_resultados.py`).

**4. ¿Por qué MapReduce no siempre es más rápido con 400 MB?**
Hadoop tiene un costo fijo alto: arrancar la JVM, planear los splits, lanzar un proceso Python por tarea, serializar todos los pares clave-valor a disco, ordenarlos (shuffle & sort) y luego reducir. Con 400 MB en una sola máquina y en modo standalone (las tareas map corren de una en una, sin paralelismo real), ese overhead pesa más que el trabajo útil, mientras que el script secuencial solo hace una pasada en memoria con un diccionario de ~120 claves. MapReduce conviene cuando los datos no caben en una máquina (cientos de GB a TB), cuando hay varios nodos para paralelizar y aprovechar la localidad de datos en HDFS, y cuando se necesita tolerancia a fallos en jobs largos.

**5. `CMD` vs `ENTRYPOINT`, y `COPY` vs `ADD`.**
`ENTRYPOINT` define el ejecutable fijo del contenedor; `CMD` define el comando o argumentos por defecto, que se reemplazan fácilmente con lo que se escriba después de `docker run imagen ...` (si hay `ENTRYPOINT`, el `CMD` se le pasa como argumentos). `COPY` solo copia archivos/directorios del contexto de build a la imagen; `ADD` hace lo mismo pero además descomprime automáticamente archivos `.tar` locales y puede descargar desde URLs. Se recomienda `COPY` salvo que se necesite explícitamente lo que hace `ADD`.

## Estructura

```
examen-p2-125052501/
├── README.md
├── .gitignore              # *.csv, .env, output/*
├── .env.example
├── docker-compose.yml
├── hadoop/
│   ├── Dockerfile
│   └── entrypoint.sh       # genera llaves ssh, levanta sshd
├── mapreduce/
│   ├── mapper.py
│   ├── reducer.py
│   ├── secuencial.py
│   └── run_job.sh          # corre Hadoop + secuencial, mide tiempos y compara
├── api/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app.py
│   └── db.py
├── scripts/
│   ├── generar_dataset.py
│   └── cargar_resultados.py
├── data/                   # aquí va el CSV (ignorado por git)
├── output/                 # salida del job (ignorada por git)
└── evidencias/
```
