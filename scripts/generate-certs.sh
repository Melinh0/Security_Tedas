#!/bin/sh
set -e

mkdir -p certs

if [ -f certs/server.key ]; then
  echo "certs/server.key ja existe; nada a fazer."
  exit 0
fi

openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout certs/server.key \
  -out certs/server.crt \
  -days 365 \
  -subj "/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"

chmod 600 certs/server.key
echo "Certificado auto-assinado gerado em certs/ (uso em desenvolvimento)."
echo "Em producao use Let's Encrypt ou um certificado emitido por autoridade."
