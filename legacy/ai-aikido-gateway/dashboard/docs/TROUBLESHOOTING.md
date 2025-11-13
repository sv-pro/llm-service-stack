# Dashboard Troubleshooting

This guide captures issues specific to the dashboard front-end and how to solve them.

---

## Playwright UI Tests

### Symptoms

Attempting to run the Playwright smoke tests (`npm run ui-test`) prints warnings similar to:

```
94.7 MiB [====================] 100% 0.0s
Webkit 26.0 (playwright build v2215) downloaded to /home/dev/.cache/ms-playwright/webkit-2215
BEWARE: your OS is not officially supported by Playwright; downloading fallback build for ubuntu22.04-x64.
Playwright Host validation warning: 
╔══════════════════════════════════════════════════════╗
║ Host system is missing dependencies to run browsers. ║
║ Please install them with the following command:      ║
║                                                      ║
║     sudo npx playwright install-deps                 ║
║                                                      ║
║ Alternatively, use apt:                              ║
║     sudo apt-get install libevent-2.1-7\             ║
║         libavif13                                    ║
║                                                      ║
║ <3 Playwright Team                                   ║
╚══════════════════════════════════════════════════════╝
```

### Root Cause

Playwright bundles its own browser binaries and expects a supported Linux distribution. Pop!\_OS is close to Ubuntu but lacks a few system libraries (`libevent-2.1-7`, `libavif13`). Without them WebKit (and sometimes Chromium) fail to launch, so tests cannot run.

### Resolution Steps

> **Platform note:** These steps were verified on **Pop!\_OS 22.04**. Other Ubuntu-derived distributions should follow the same commands; non-Debian systems may require different package names.

1. **Install the missing OS packages**
   ```bash
   sudo apt-get update
   sudo apt-get install libevent-2.1-7 libavif13
   ```
   Alternatively run the convenience helper:
   ```bash
   # If npx is unavailable, prefix with the installed Node.js path.
   # Example for Node managed via nvm:
   #   sudo /usr/bin/env PATH="$PATH" npx playwright install-deps
   sudo npx playwright install-deps
   ```

2. **Reinstall browser binaries for the current user**
   ```bash
   cd dashboard
   npx playwright install
   ```

3. **Run the tests**
   - Start the dashboard (`npm run dev`) or set `PLAYWRIGHT_WEB_SERVER=true`.
     - Either export the variable (`export PLAYWRIGHT_WEB_SERVER=true`) prior to running the tests, or pass it inline to a single command (`PLAYWRIGHT_WEB_SERVER=true npm run ui-test`).
   - Execute `npm run ui-test` (or the top-level shortcuts `make ui-tests-pw` / `make ui-tests-pw-show`).
     - `make ui-tests-pw-show` runs headed with a default slow motion; override via `PLAYWRIGHT_SLOWMO=100 make ui-tests-pw-show` (alias `PLAYWRIGHT_SLOW_MO`).
   - To generate an HTML report, run `make ui-test ARGS="--reporter=html"` then `npx playwright show-report` from the `dashboard/` directory.

### Additional Notes

- If the host remains unsupported, consider running the tests inside a container (Playwright publishes Docker images with all dependencies).
- When using CI, ensure the runner either installs the dependencies above or leverages the `playwright install-deps` helper before invoking the test command.

---

## Re^Re Loop Demo shows "Disconnected" or "Websocket connection error"

**Symptom:**

When you start the Re^Re Loop Demo, the status immediately shows "Disconnected" or "Websocket connection error". The browser's developer console may show errors like `403 Forbidden` or `NS_ERROR_WEBSOCKET_CONNECTION_REFUSED` for the WebSocket connection attempt.

**Root Cause:**

This issue occurs when the frontend application tries to connect to the wrong WebSocket URL. The backend API routes are prefixed with `/v1`, and the WebSocket endpoint is no exception. The frontend code must include this prefix when constructing the URL.

- **Incorrect URL:** `ws://<host>:<port>/ws/re-re/<execution_id>`
- **Correct URL:** `ws://<host>:<port>/v1/ws/re-re/<execution_id>`

**Solution:**

1.  Open the frontend file responsible for the WebSocket connection: `dashboard/src/hooks/useTelemetry.js`.
2.  Locate the `connect` function within the hook.
3.  Find the line where the `wsUrl` constant is defined.
4.  Ensure that the URL is constructed with the `/v1` prefix. It should look like this:
    ```javascript
    const wsUrl = `ws://127.0.0.1:8000/v1/ws/re-re/${executionId}`;
    ```
    *(Note: The host and port might be different in your environment, but the path should be correct).*
5.  After saving the file, rebuild the dashboard:
    ```bash
    npm run build
    ```
6.  Restart the dashboard container to serve the updated files.
7.  Clear your browser cache before testing again.
