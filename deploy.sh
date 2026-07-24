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

# Guardián: los comentarios Django {# #} partidos en varias líneas se imprimen
# como texto visible en la página. Si existe alguno, se cancela el deploy.
fugas=$(grep -rn '{#' --include='*.html' apps templates 2>/dev/null | grep -v '#}' || true)
if [ -n "$fugas" ]; then
  echo "✗ DEPLOY CANCELADO — comentarios Django multilínea (se verían como texto):"
  echo "$fugas"
  exit 1
fi

echo "→ Desplegando Don Chugo en $VPS ..."
ssh -o ConnectTimeout=10 "$VPS" '
  set -e
  cd /root/DON_CHUGO
  git fetch origin
  echo "── Commits nuevos que se van a aplicar ──"
  git log HEAD..origin/main --oneline
  git pull --ff-only
  grep -q "^HTTPS_ENABLED=" .env || echo "HTTPS_ENABLED=True" >> .env
  # El VPS usa Docker Compose v2 (docker compose); local usa v1 (docker-compose)
  docker compose up --build -d
  echo "── Estado de los contenedores ──"
  docker compose ps
'

echo "→ Verificando $URL (el contenedor tarda ~20s en migrar y arrancar) ..."
for intento in 1 2 3 4 5 6; do
  sleep 10
  code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 20 "$URL" || echo 000)
  if [ "$code" = "200" ] || [ "$code" = "302" ]; then
    echo "✅ Deploy OK — $URL respondió HTTP $code"
    exit 0
  fi
  echo "   intento $intento: HTTP $code, reintentando..."
done

echo "⚠️  $URL no respondió tras 60s — revisa los logs con:"
echo "    ssh $VPS 'cd /root/DON_CHUGO && docker compose logs --tail 50 web'"
exit 1
