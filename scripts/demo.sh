#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
API_URL=${API_URL:-http://localhost:8000}
UI_URL=${UI_URL:-http://localhost:3000}
PLAYBOOK_NAME=${PLAYBOOK_NAME:-SaaS Credential Stuffing Campaign}
ADMIN_EMAIL=${ADMIN_EMAIL:-admin@example.com}
ADMIN_PASSWORD=${ADMIN_PASSWORD:-ChangeMe123!}
WAIT_SECONDS=${WAIT_SECONDS:-180}
POLL_INTERVAL=${POLL_INTERVAL:-5}
COMPOSE_ARGS=${COMPOSE_ARGS:-}

command -v docker >/dev/null 2>&1 || { echo "[demo] docker is required" >&2; exit 1; }
command -v curl >/dev/null 2>&1 || { echo "[demo] curl is required" >&2; exit 1; }
command -v jq >/dev/null 2>&1 || { echo "[demo] jq is required" >&2; exit 1; }

export DOCKER_BUILDKIT=1

cat <<EOF
[demo] Bringing up the Threat Hunting Playbooks stack…
  • API URL: $API_URL
  • UI URL:  $UI_URL
  • Playbook: "$PLAYBOOK_NAME"
EOF

( cd "$ROOT_DIR" && docker compose up -d --build $COMPOSE_ARGS )

cat <<'EOF'
[demo] Waiting for containers to report healthy services…
EOF

declare -r deadline=$((SECONDS + WAIT_SECONDS))
while (( SECONDS < deadline )); do
  if curl -sSf "$API_URL/health" >/dev/null; then
    echo "[demo] API is healthy."
    break
  fi
  sleep "$POLL_INTERVAL"
done

if (( SECONDS >= deadline )); then
  echo "[demo] Timeout reached while waiting for API readiness" >&2
  exit 1
fi

cat <<'EOF'
[demo] Requesting access token for the seeded administrator account…
EOF

auth_response=$(curl -sS -X POST "$API_URL/api/auth/token" \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode "username=$ADMIN_EMAIL" \
  --data-urlencode "password=$ADMIN_PASSWORD")

token=$(jq -r '.access_token // empty' <<<"$auth_response")
if [[ -z "$token" ]]; then
  echo "[demo] Failed to acquire access token:" >&2
  echo "$auth_response" >&2
  exit 1
fi

echo "[demo] Access token acquired. Listing available playbooks…"

playbooks_json=$(curl -sS -H "Authorization: Bearer $token" "$API_URL/api/playbooks/")
playbook_id=$(jq -r --arg name "$PLAYBOOK_NAME" '.[] | select(.name==$name) | .id' <<<"$playbooks_json" | head -n 1)

if [[ -z "$playbook_id" || "$playbook_id" == "null" ]]; then
  echo "[demo] Playbook named '$PLAYBOOK_NAME' was not found. Available playbooks:" >&2
  echo "$playbooks_json" | jq -r '.[].name'
  exit 1
fi

echo "[demo] Running playbook $playbook_id ($PLAYBOOK_NAME)…"

run_response=$(curl -sS -X POST \
  "$API_URL/api/playbooks/$playbook_id/run" \
  -H 'Authorization: Bearer '$token \
  -H 'Content-Type: application/json')

matches=$(jq -r '.result.matched_count' <<<"$run_response")
total=$(jq -r '.result.total_records' <<<"$run_response")
confidence=$(jq -r '.result.confidence' <<<"$run_response")
notes=$(jq -r '.result.execution_notes' <<<"$run_response")

cat <<EOF
[demo] Hunt complete ✅
  • Matches:    ${matches:-?}
  • Total:      ${total:-?}
  • Confidence: ${confidence:-?}
  • Notes:      ${notes:-?}
EOF

output_dir="$ROOT_DIR/.demo-output"
mkdir -p "$output_dir"
run_file="$output_dir/${playbook_id}_run.json"
telemetry_events="$output_dir/telemetry_events.json"
telemetry_alerts="$output_dir/telemetry_alerts.json"

echo "$run_response" | jq '.' > "$run_file"

curl -sS -H "Authorization: Bearer $token" "$API_URL/api/telemetry/events?limit=3" | jq '.' > "$telemetry_events"
curl -sS -H "Authorization: Bearer $token" "$API_URL/api/telemetry/alerts?limit=3" | jq '.' > "$telemetry_alerts"

echo "[demo] Artifacts captured in $output_dir:" \
  && ls -1 "$output_dir"

cat <<EOF

Next steps:
  1. Open the UI dashboard → $UI_URL (use the token below for bearer auth).
  2. Inspect recent telemetry: cat $telemetry_events
  3. Re-run hunts or explore other playbooks with:
     THREAT_API_URL=$API_URL THREAT_API_TOKEN=$token threat-cli list

Bearer token (valid for ~60 minutes):
$token
EOF
