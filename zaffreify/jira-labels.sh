#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: jira-labels.sh <area|scrum>" >&2
  exit 1
}

[[ $# -lt 1 ]] && usage

MODE="$1"
ENV_FILE="$(cd "$(dirname "$0")/.." && pwd)/.env"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Error: $ENV_FILE not found. Copy .env.example and fill in credentials." >&2
  exit 1
fi

source "$ENV_FILE"

for var in JIRA_EMAIL JIRA_TOKEN JIRA_HOST; do
  if [[ -z "${!var:-}" ]]; then
    echo "Error: $var is not set in $ENV_FILE" >&2
    exit 1
  fi
done

AUTH="Authorization: Basic $(echo -n "${JIRA_EMAIL}:${JIRA_TOKEN}" | base64)"
ENDPOINT="https://${JIRA_HOST}/rest/api/2/jql/autocompletedata/suggestions"

query_labels() {
  local prefix="$1"
  curl -sf -G "$ENDPOINT" \
    -H "$AUTH" \
    -H "Accept: application/json" \
    --data-urlencode "fieldName=labels" \
    --data-urlencode "fieldValue=$prefix" 2>/dev/null \
  | python3 -c '
import json, sys
data = json.load(sys.stdin)
for r in data.get("results", []):
    v = r.get("value", "")
    if v:
        print(v)
' 2>/dev/null || true
}

case "$MODE" in
  area)
    for letter in {a..z}; do
      query_labels "dashboard-area-${letter}"
    done | grep '^dashboard-area-' | sort -u
    ;;
  scrum)
    for letter in {a..z}; do
      query_labels "dashboard-${letter}"
    done | grep -E '^dashboard-.*-scrum$' | sort -u
    ;;
  *)
    usage
    ;;
esac
