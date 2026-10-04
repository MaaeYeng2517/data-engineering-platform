#!/bin/sh
# Store the Grafana Cloud Prometheus push token outside of git.
#
#   ./scripts/configure-grafana-cloud.sh <push-token>
#
# The endpoint and org id live in .env; only the token is written to a file that
# docker/prometheus reads at start-up.
set -eu

TOKEN="${1:-}"

if [ -z "$TOKEN" ]; then
    echo "usage: $0 <grafana-cloud-prometheus-push-token>" >&2
    echo "create one at Grafana Cloud -> Prometheus -> Remote write" >&2
    exit 1
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SECRET_DIR="$ROOT/docker/prometheus/secrets"
SECRET_FILE="$SECRET_DIR/grafana-cloud.password"

mkdir -p "$SECRET_DIR"
umask 077
printf '%s' "$TOKEN" >"$SECRET_FILE"

# The Prometheus container runs as uid 65534 (nobody), so the file has to be
# readable by it. A Docker bind mount keeps the host mode, hence 0444 here; the
# file stays outside git via .gitignore.
chmod 0444 "$SECRET_FILE"

echo "wrote token to $SECRET_FILE (mode $(stat -f '%Lp' "$SECRET_FILE"))"
echo "next: set GRAFANA_CLOUD_REMOTE_WRITE_URL and GRAFANA_CLOUD_ORG_ID in .env, then"
echo "  docker compose --profile catalog --profile tools --profile production up -d prometheus"