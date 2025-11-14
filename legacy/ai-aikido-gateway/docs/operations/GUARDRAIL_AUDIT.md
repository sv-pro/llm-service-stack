# Guardrail Audit Workflow

This guide explains how to verify that gateway guard rails reject requests when provider API keys are absent and recover once keys are reintroduced.

## Prerequisites
- Docker Compose stack (`make docker-up`) or a local uvicorn instance.
- Access to `scripts/guardrail_review.sh` and `scripts/guardrail_audit.sh`.
- Gateway exposed at `http://localhost:8000` (override via env vars).

## Key Environment Variables
- `REDEPLOY_CMD` – command to restart the gateway, e.g. `make docker-redeploy`.
- `HEALTH_URL` – health endpoint (`http://localhost:8000/health` by default).
- `CHAT_URL` – chat completions endpoint (`http://localhost:8000/v1/chat/completions`).
- `EXPECT_WHEN_DISABLED` – expected HTTP status when keys are missing (default `400`).
- `AUDIT_LOG` – output log file (default `/tmp/guardrail_audit.log`).

## Automated Run
```bash
# Start or ensure the gateway is running
make docker-up

# Execute the audit
REDEPLOY_CMD="make docker-redeploy" scripts/guardrail_audit.sh

# Review the log
cat /tmp/guardrail_audit.log
```

The script performs the following:
1. Baseline request expecting HTTP 200.
2. Clears gateway-owned provider keys.
3. Runs `REDEPLOY_CMD` (if set) and waits for the health endpoint.
4. Sends a request expecting `EXPECT_WHEN_DISABLED` (default 400).
5. Restores `.env` from the latest `bak/guardrail` backup.
6. Redeploys again and checks for HTTP 200.

## Manual Workflow
1. `scripts/guardrail_review.sh backup-env`
2. `scripts/guardrail_review.sh disable-provider-keys`
3. Restart the gateway (`make docker-redeploy` or manual command).
4. `scripts/guardrail_review.sh send-request --expect-status 400`
5. `scripts/guardrail_review.sh restore-env`
6. Restart and verify `--expect-status 200`

## Tips
- `.env` is optional for Docker: supply `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` via environment variables.
- Use `GATEWAY_DATA_DIR=$PWD/data` when running uvicorn locally so SQLite files are writable.
- Generated backups live in `bak/guardrail/`; `restore-env` picks the newest backup when no path is provided.

