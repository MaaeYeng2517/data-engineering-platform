#!/bin/sh
# Prometheus entrypoint that optionally ships metrics to Grafana Cloud.
#
# Prometheus cannot expand environment variables inside prometheus.yml, so the
# remote_write block is rendered here from GRAFANA_CLOUD_* variables. When no
# push token is mounted the block is omitted and Prometheus behaves exactly as
# before — the integration is opt-in.
set -eu

CONFIG_SRC=/etc/prometheus/prometheus.yml
CONFIG_DST=/etc/prometheus/prometheus.rendered.yml
PASSWORD_FILE="${GRAFANA_CLOUD_PASSWORD_FILE:-/etc/prometheus/grafana-cloud.password}"
REMOTE_WRITE_URL="${GRAFANA_CLOUD_REMOTE_WRITE_URL:-}"
ORG_ID="${GRAFANA_CLOUD_ORG_ID:-}"

cp "$CONFIG_SRC" "$CONFIG_DST"

if [ -s "$PASSWORD_FILE" ] && [ -n "$REMOTE_WRITE_URL" ] && [ -n "$ORG_ID" ]; then
    # The endpoint and org id are not secrets, so they stay inline. Only the
    # token comes from the mounted file.
    cat >>"$CONFIG_DST" <<EOF

remote_write:
  - url: "${REMOTE_WRITE_URL}"
    basic_auth:
      username: "${ORG_ID}"
      password_file: ${PASSWORD_FILE}
EOF
    echo "grafana-cloud: remote_write enabled -> ${REMOTE_WRITE_URL} (org ${ORG_ID})"
elif [ -n "$REMOTE_WRITE_URL" ] || [ -s "$PASSWORD_FILE" ]; then
    echo "grafana-cloud: incomplete configuration, remote_write disabled" >&2
    echo "grafana-cloud: need REMOTE_WRITE_URL + ORG_ID + a non-empty push token" >&2
else
    echo "grafana-cloud: no push token mounted, remote_write disabled"
fi

exec /bin/prometheus \
    --config.file="$CONFIG_DST" \
    --storage.tsdb.path=/prometheus \
    --web.console.libraries=/etc/prometheus/console_libraries \
    --web.console.templates=/etc/prometheus/consoles \
    --web.enable-lifecycle