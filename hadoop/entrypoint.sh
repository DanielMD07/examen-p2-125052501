#!/bin/bash
# Arranque del contenedor hadoop:
#  1. Genera (una sola vez) el par de llaves ssh en el volumen compartido /keys
#  2. Autoriza esa llave para el usuario hadoop (ssh sin contrasena)
#  3. Levanta sshd y deja el contenedor vivo
set -e

if [ ! -f /keys/id_rsa ]; then
    ssh-keygen -t rsa -b 4096 -P '' -f /keys/id_rsa -C "hadoop@examen-p2"
fi

install -d -m 700 -o hadoop -g hadoop /home/hadoop/.ssh
install -m 600 -o hadoop -g hadoop /keys/id_rsa     /home/hadoop/.ssh/id_rsa
install -m 644 -o hadoop -g hadoop /keys/id_rsa.pub /home/hadoop/.ssh/id_rsa.pub
install -m 600 -o hadoop -g hadoop /keys/id_rsa.pub /home/hadoop/.ssh/authorized_keys
printf 'Host *\n    StrictHostKeyChecking accept-new\n' > /home/hadoop/.ssh/config
chown hadoop:hadoop /home/hadoop/.ssh/config

# Llaves de host: se generan una vez y se guardan en el volumen (no van
# horneadas en la imagen) para que no cambien si se recrea el contenedor
if [ ! -f /keys/host/ssh_host_ed25519_key ]; then
    mkdir -p /keys/host
    ssh-keygen -t ed25519 -N '' -f /keys/host/ssh_host_ed25519_key
fi
rm -f /etc/ssh/ssh_host_*
cp /keys/host/ssh_host_ed25519_key* /etc/ssh/
chmod 600 /etc/ssh/ssh_host_ed25519_key
/usr/sbin/sshd

echo "hadoop listo: sshd corriendo, $(hadoop version | head -1)"
exec sleep infinity
