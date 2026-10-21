#!/bin/sh
set -e

mkdir -p /app/public/static /app/public/media /app/private-media

# Named/bind volumes are often root-owned; fix then drop privileges.
if [ "$(id -u)" = "0" ]; then
  chown -R appuser:appuser /app/public /app/private-media
  exec gosu appuser "$0" "$@"
fi

python manage.py migrate --noinput
python manage.py collectstatic --noinput
exec "$@"
