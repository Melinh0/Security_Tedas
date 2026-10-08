#!/bin/sh
set -e

echo "Aguardando banco de dados..."
tries=0
until python manage.py migrate --noinput; do
  tries=$((tries + 1))
  if [ "$tries" -ge 30 ]; then
    echo "Banco indisponivel apos 30 tentativas." >&2
    exit 1
  fi
  echo "Banco ainda indisponivel ($tries/30), tentando em 2s..."
  sleep 2
done

python manage.py collectstatic --noinput

echo "Iniciando gunicorn..."
exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers "${GUNICORN_WORKERS:-3}" \
  --access-logfile - \
  --error-logfile -
