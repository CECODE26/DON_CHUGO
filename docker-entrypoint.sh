#!/bin/sh
set -e

python - <<'PY'
import os
import socket
import sys
import time

host = os.environ.get("MYSQL_HOST", "db")
port = int(os.environ.get("MYSQL_PORT", "3306"))
timeout = int(os.environ.get("DB_WAIT_TIMEOUT", "60"))
deadline = time.time() + timeout
last_error = None

while time.time() < deadline:
    try:
        with socket.create_connection((host, port), timeout=5):
            sys.exit(0)
    except OSError as exc:
        last_error = exc
        time.sleep(2)

print(f"Database not ready: {last_error}", file=sys.stderr)
sys.exit(1)
PY

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec "$@"