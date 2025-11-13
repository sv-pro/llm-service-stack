AI Aikido Gateway - Testing Guide
=================================

The project uses `pytest` for unit, integration, and end-to-end (E2E) coverage.
All suites are runnable locally with no external LLM credentials by relying on
fixtures and monkeypatching.

## Running the test suite

- Run everything: `pytest -q`
- Focus on E2E coverage (gateway + plugin pipeline): `pytest tests/test_end_to_end.py -q`
- Show verbose logs while diagnosing: `pytest -vv --log-cli-level=INFO`

CI executes `pytest` from the repository root, so any test under `tests/`
automatically participates.

### CI prerequisites

- Ensure `litellm>=1.35.7` is installed; it is listed in both `requirements.txt` and `pyproject.toml`.
- No provider API keys are required for automated suites—the end-to-end tests monkeypatch LiteLLM and redirect SQLite paths.
- Pydantic emits deprecation warnings from LiteLLM; they are harmless but can be filtered if desired (`PYTHONWARNINGS=ignore::DeprecationWarning`).

## End-to-end tests

`tests/test_end_to_end.py` exercises the FastAPI app, plugin pipeline, and LiteLLM
integration using the real routing code paths. The suite:

- Spins up the FastAPI `app` through `TestClient`, so plugin startup/shutdown hooks fire.
- Monkeypatches LiteLLM responses to avoid network calls.
- Redirects cache/history SQLite plugins to temporary files so assertions can verify
  that responses and metadata persist across requests.
- Covers primary OpenAI, fallback, Anthropic, and failure/error flows. Failure cases
  now assert that retry metadata is surfaced through transparency headers even when
  the request terminates with a 5xx.

When adding new gateway behaviour, prefer expressing it in these E2E tests so the
full plugin stack is validated.

## Persistence checks

The helpers in the test module (`_get_history_entries`, `_get_cache_entries`) open the
temporary SQLite files and read back written rows. Use the same pattern when adding
assertions for new plugins that persist data.

## Troubleshooting tips

- If end-to-end tests hang, ensure no background coroutine `sleep` calls remain;
  the suite already monkeypatches `asyncio.sleep` to a no-op.
- The temporary SQLite files live in `tmp_path`; dumping their contents during
  development can clarify persistence issues, but avoid committing debug prints.
- The OpenAI and Anthropic proxy plugins disable themselves automatically when
  no API keys are configured. Tests re-enable them via fixtures—do the same in
  custom test helpers if you need to inject fake key pools.

## UI tests (Playwright)

- Location: `dashboard/tests/ui`
- Command: `cd dashboard && npm run ui-test` (top-level: `make ui-test`, auto-start: `make ui-tests-pw`, headed+slow-mo: `make ui-tests-pw-show`)
- Requirements:
  - Install dependencies via `npm install` after pulling new changes.
  - Install Playwright dependencies once via `cd dashboard && npx playwright install`.
  - Ensure the dashboard is running on `http://localhost:3000` (or set `PLAYWRIGHT_BASE_URL`).
- Optional: set `PLAYWRIGHT_WEB_SERVER=true` to let Playwright start `npm run dev` automatically.
- Optional environment overrides:
  - `PLAYWRIGHT_SLOWMO=<ms>` (alias `PLAYWRIGHT_SLOW_MO`) controls launch slow motion (default 200 ms in `make ui-tests-pw-show`).
  - `PLAYWRIGHT_TEST_TIMEOUT=<ms>` changes the per-test timeout.
  - `PLAYWRIGHT_REPORTER=html` (or any comma-separated reporters) switches the report output.
- Pass extra CLI args via `make ui-test ARGS="--project=webkit"` (propagates to all UI targets). For HTML reports use `make ui-test ARGS="--reporter=html"` then `npx playwright show-report`.
- Current smoke coverage:
  - `navigation.spec.ts` – verifies Cost Explorer navigation is reachable.
  - `playground.spec.ts` – confirms default redirect and returning to Playground.
  - `request-history.spec.ts` – exercises sidebar navigation and ensures the page renders (stats cards or error state).
- Output directories such as `playwright-report/` and `test-results/` are gitignored.
