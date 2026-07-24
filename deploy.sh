#!/usr/bin/env bash
# Despliegue de Don Chugo al VPS (Rocky Linux 9, Contabo).
#
# Uso:  ./deploy.sh
#
# Qué hace:
#   1. Entra al VPS por SSH
#   2. git pull de los últimos commits de main (solo fast-forward)
#   3. Reconstruye la imagen Docker y levanta el stack
#      (restart NO basta: el código va copiado dentro de la imagen)
#   4. Verifica desde tu máquina que https://dccoffe.store responda
set -euo pipefail

VPS="root@31.220.98.255"
URL="https://dccoffe.store"

echo "→ Desplegando Don Chugo en $VPS ..."
ssh -o ConnectTimeout=10 "$VPS" '
  set -e
  cd /root/DON_CHUGO
  git fetch origin
  echo "── Commits nuevos que se van a aplicar ──"
  git log HEAD..origin/main --oneline
  git pull --ff-only
  grep -q "^HTTPS_ENABLED=" .env || echo "HTTPS_ENABLED=True" >> .env
  docker-compose up --build -d
  echo "── Estado de los contenedores ──"
  docker-compose ps
'

echo "→ Verificando $URL ..."
sleep 5
code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 20 "$URL")
if [ "$code" = "200" ] || [ "$code" = "302" ]; then
  echo "✅ Deploy OK — $URL respondió HTTP $code"
else
  echo "⚠️  $URL respondió HTTP $code — revisa los logs con:"
  echo "    ssh $VPS 'cd /root/DON_CHUGO && docker-compose logs --tail 50 web'"
  exit 1
fi
