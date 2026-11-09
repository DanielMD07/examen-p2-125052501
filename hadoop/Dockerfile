# syntax=docker/dockerfile:1
FROM debian:12

ARG HADOOP_VERSION=3.3.6
# UID del usuario hadoop = UID del usuario del host, para que los archivos
# que escribe el job en ./output no queden como root
ARG HADOOP_UID=1000

# Java (JDK 17), Python 3 para Hadoop Streaming y OpenSSH Server
RUN apt-get update && apt-get install -y --no-install-recommends \
        openjdk-17-jdk-headless \
        python3 \
        openssh-server openssh-client \
        wget ca-certificates procps \
    && rm -rf /var/lib/apt/lists/*

# Variables de entorno de Hadoop
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 \
    HADOOP_HOME=/opt/hadoop
ENV HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop \
    PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin

# Instalacion de Hadoop (modo standalone: no se configura nada mas).
# Si hadoop-X.tar.gz esta junto a este Dockerfile se usa ese (montado, sin
# agregar capas); si no, se descarga de Apache.
RUN --mount=type=bind,source=.,target=/ctx \
    TGZ=hadoop-${HADOOP_VERSION}.tar.gz; \
    if [ -f /ctx/$TGZ ]; then cp /ctx/$TGZ /tmp/; \
    else wget -q -P /tmp https://dlcdn.apache.org/hadoop/common/hadoop-${HADOOP_VERSION}/$TGZ \
      || wget -q -P /tmp https://archive.apache.org/dist/hadoop/common/hadoop-${HADOOP_VERSION}/$TGZ; fi \
    && tar -xzf /tmp/$TGZ -C /opt \
    && ln -s /opt/hadoop-${HADOOP_VERSION} $HADOOP_HOME \
    && rm /tmp/$TGZ \
    && rm -rf $HADOOP_HOME/share/doc \
    && echo "export JAVA_HOME=$JAVA_HOME" >> $HADOOP_CONF_DIR/hadoop-env.sh

# Las sesiones SSH no heredan los ENV de Docker: se replican en /etc/profile.d
RUN printf 'export JAVA_HOME=%s\nexport HADOOP_HOME=%s\nexport HADOOP_CONF_DIR=%s\nexport PATH=$PATH:%s/bin:%s/sbin\n' \
        "$JAVA_HOME" "$HADOOP_HOME" "$HADOOP_CONF_DIR" "$HADOOP_HOME" "$HADOOP_HOME" \
        > /etc/profile.d/hadoop.sh

# Usuario hadoop SIN contrasena (--disabled-password): solo entra con llave
RUN useradd -m -s /bin/bash -u ${HADOOP_UID} hadoop \
    && passwd -l hadoop \
    && sed -i '1i . /etc/profile.d/hadoop.sh' /home/hadoop/.bashrc \
    && chown -R hadoop:hadoop /opt/hadoop-${HADOOP_VERSION}

# sshd: solo llaves, nada de contrasenas, root no entra
RUN mkdir -p /run/sshd \
    && sed -i 's/^#\?PasswordAuthentication .*/PasswordAuthentication no/' /etc/ssh/sshd_config \
    && sed -i 's/^#\?PermitRootLogin .*/PermitRootLogin no/' /etc/ssh/sshd_config \
    && sed -i 's/^#\?PubkeyAuthentication .*/PubkeyAuthentication yes/' /etc/ssh/sshd_config

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

WORKDIR /opt/mapreduce
EXPOSE 22

ENTRYPOINT ["/entrypoint.sh"]
