#!/usr/bin/env bash
set -euo pipefail

AUDIT_LOG=${AUDIT_LOG:-/tmp/guardrail_audit.log}
REDEPLOY_CMD=${REDEPLOY_CMD:-}
HEALTH_URL=${HEALTH_URL:-http://localhost:8000/health}
CHAT_URL=${CHAT_URL:-http://localhost:8000/v1/chat/completions}
BASELINE_MODEL=${BASELINE_MODEL:-gpt-3.5-turbo}
BASELINE_PROMPT=${BASELINE_PROMPT:-"Guardrail audit baseline ping"}
EXPECT_WHEN_DISABLED=${EXPECT_WHEN_DISABLED:-400}

log() {
  local msg="[guardrail-audit] $1"
  echo "$msg" | tee -a "$AUDIT_LOG"
}

run_cmd() {
  log "Running: $*"
  "$@" | tee -a "$AUDIT_LOG"
}

wait_for_gateway() {
  log "Waiting for gateway health at $HEALTH_URL"
  local tries=0
  until curl -fsS "$HEALTH_URL" >/dev/null 2>&1; do
    tries=$((tries + 1))
    if [ $tries -ge 30 ]; then
      log "Gateway did not become healthy within timeout"
      return 1
    fi
    sleep 2
  done
  log "Gateway reported healthy"
}

send_request_expect() {
  local status="$1"
  shift
  log "Expecting HTTP $status from $CHAT_URL"
  if scripts/guardrail_review.sh send-request --url "$CHAT_URL" --model "$BASELINE_MODEL" --prompt "$BASELINE_PROMPT" --expect-status "$status" "$@" | tee -a "$AUDIT_LOG"; then
    log "Request completed with expected status $status"
  else
    log "Request failed or returned unexpected status"
    exit 1
  fi
}

redeploy_if_needed() {
  if [ -n "$REDEPLOY_CMD" ]; then
    log "Redeploying via: $REDEPLOY_CMD"
    if $REDEPLOY_CMD | tee -a "$AUDIT_LOG"; then
      log "Redeploy command finished"
    else
      log "Redeploy command failed"
      exit 1
    fi
  else
    log "REDEPLOY_CMD not set; skipping redeploy"
  fi
}

printf '' > "$AUDIT_LOG"
log "=== Guardrail audit started $(date) ==="

wait_for_gateway
send_request_expect 200

log "Disabling provider keys"
run_cmd scripts/guardrail_review.sh disable-provider-keys
redeploy_if_needed
wait_for_gateway
send_request_expect "$EXPECT_WHEN_DISABLED"

log "Restoring provider keys"
run_cmd scripts/guardrail_review.sh restore-env
redeploy_if_needed
wait_for_gateway
send_request_expect 200

log "=== Guardrail audit completed $(date) ==="
