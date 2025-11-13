#!/usr/bin/env bash
set -eo pipefail

BACKUP_DIR="bak/guardrail"
ENV_FILE=".env"
TMP_DIR="${TMPDIR:-/tmp}"
DEFAULT_ENDPOINT="${GATEWAY_URL:-http://localhost:8000}/v1/chat/completions"

usage() {
  cat <<USAGE
Usage: $0 <command> [options]

Commands:
  backup-env                 Create a timestamped backup of .env under ${BACKUP_DIR}/
  disable-provider-keys      Replace provider API keys in .env with empty values
  restore-env [path|prefix]  Restore .env from a backup (default: most recent)
  send-request [options]     Send a sample request to the gateway and print result

Options for send-request:
  --url <url>                Gateway chat endpoint (default: ${DEFAULT_ENDPOINT})
  --model <model>            Model to request (default: gpt-3.5-turbo)
  --prompt <text>            Prompt to send (default: "Ping from guardrail review")
  --expect-status <code>     Expect HTTP status; exit non-zero if mismatch

Examples:
  $0 backup-env
  $0 disable-provider-keys
  $0 send-request --expect-status 503
  $0 restore-env
  $0 restore-env .env.20251027-120000
USAGE
}

log() {
  printf 'guardrail-review: %s\n' "$1"
}

ensure_env() {
  if [ ! -f "$ENV_FILE" ]; then
    echo "Error: $ENV_FILE not found" >&2
    exit 1
  fi
}

backup_env() {
  ensure_env
  mkdir -p "$BACKUP_DIR"
  local stamp
  stamp=$(date '+%Y%m%d-%H%M%S')
  local dest="$BACKUP_DIR/.env.${stamp}"
  cp "$ENV_FILE" "$dest"
  log "Backed up $ENV_FILE to $dest"
}

sanitize_env() {
  ensure_env
  cp "$ENV_FILE" "${ENV_FILE}.tmp"
  sed -E -i '' -e 's/^(OPENAI_API_KEY=).*/\1/' -e 's/^(ANTHROPIC_API_KEY=).*/\1/' "${ENV_FILE}.tmp" 2>/dev/null || \
    sed -E -i -e 's/^(OPENAI_API_KEY=).*/\1/' -e 's/^(ANTHROPIC_API_KEY=).*/\1/' "${ENV_FILE}.tmp"
  mv "${ENV_FILE}.tmp" "$ENV_FILE"
  log "Provider API keys cleared in $ENV_FILE"
}

restore_env() {
  local input="$1"
  local candidate=""

  if [ -n "$input" ]; then
    if [ -f "$input" ]; then
      candidate="$input"
    elif [ -f "$BACKUP_DIR/$input" ]; then
      candidate="$BACKUP_DIR/$input"
    else
      shopt -s nullglob
      local matches=( "$BACKUP_DIR/$input"* )
      shopt -u nullglob
      if [ ${#matches[@]} -gt 0 ]; then
        candidate="${matches[0]}"
      fi
    fi
    if [ -z "$candidate" ]; then
      echo "Error: backup matching '$input' not found" >&2
      exit 1
    fi
  else
    candidate=$(ls -1t "$BACKUP_DIR"/.env.* 2>/dev/null | head -n1)
    if [ -z "$candidate" ]; then
      echo "Error: no backups found under $BACKUP_DIR" >&2
      exit 1
    fi
  fi

  cp "$candidate" "$ENV_FILE"
  log "Restored $ENV_FILE from $candidate"
}

send_request() {
  local url="$DEFAULT_ENDPOINT"
  local model="gpt-3.5-turbo"
  local prompt="Ping from guardrail review"
  local expect=""

  while [ $# -gt 0 ]; do
    case "$1" in
      --url)
        url="$2"; shift 2;;
      --model)
        model="$2"; shift 2;;
      --prompt)
        prompt="$2"; shift 2;;
      --expect-status)
        expect="$2"; shift 2;;
      *)
        echo "Unknown option: $1" >&2
        usage
        exit 1;;
    esac
  done

  local payload
  payload=$(GUARDRAIL_MODEL="$model" GUARDRAIL_PROMPT="$prompt" python - <<'PY'
import json, os, sys
model = os.environ.get('GUARDRAIL_MODEL')
prompt = os.environ.get('GUARDRAIL_PROMPT')
payload = {
    "model": model,
    "messages": [{"role": "user", "content": prompt}],
    "temperature": 0.7,
    "max_completion_tokens": 1000,
}
print(json.dumps(payload))
PY
)

  log "POST $url"
  local response_file="$TMP_DIR/guardrail_response.json"
  rm -f "$response_file"

  local http_code
  local curl_status=0
  http_code=$(curl -sS -o "$response_file" -w '%{http_code}' -H 'Content-Type: application/json' -X POST "$url" -d "$payload" ) || curl_status=$?

  if [ $curl_status -ne 0 ]; then
    echo "curl failed with exit code $curl_status. See logs above." >&2
    exit 1
  fi

  log "HTTP $http_code"
  if [ -f "$response_file" ]; then
    cat "$response_file"
    echo
  fi

  if [ -n "$expect" ] && [ "$http_code" != "$expect" ]; then
    echo "Expected status $expect but got $http_code" >&2
    exit 2
  fi
}

command="$1"
shift || true

case "$command" in
  backup-env)
    backup_env;;
  disable-provider-keys)
    backup_env
    sanitize_env;;
  restore-env)
    restore_env "$1";;
  send-request)
    send_request "$@";;
  ""|-h|--help)
    usage;;
  *)
    echo "Unknown command: $command" >&2
    usage
    exit 1;;
esac
