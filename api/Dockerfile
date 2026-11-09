FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Cliente ssh para demostrar el acceso api -> hadoop
RUN apt-get update && apt-get install -y --no-install-recommends openssh-client \
    && rm -rf /var/lib/apt/lists/* \
    && printf 'Host hadoop\n    User hadoop\n    IdentityFile /keys/id_rsa\n    StrictHostKeyChecking accept-new\n' > /etc/ssh/ssh_config.d/hadoop.conf

WORKDIR /app

# Primero las dependencias, para aprovechar la cache de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py db.py ./

EXPOSE 8000

CMD ["python", "app.py"]
