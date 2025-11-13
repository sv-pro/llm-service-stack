import React, { useEffect, useState } from 'react';
import './Settings.css';
import API_URL from '../config';

const GATEWAY_URL = API_URL;

const COMMAND_SECTIONS = [
  {
    title: 'Gateway & Dashboard',
    description: 'Common commands to start the local stack backed by Docker compose.',
    commands: [
      { label: 'Start stack', value: 'make docker-up' },
      { label: 'Stop stack', value: 'make docker-down' },
      { label: 'Redeploy', value: 'make docker-redeploy' },
    ],
  },
  {
    title: 'Playwright UI Tests',
    description: 'Transparent CLI modes to validate dashboard flows in headless or headed mode.',
    commands: [
      { label: 'Headless auto server', value: 'make ui-tests-pw' },
      { label: 'Headed slow motion', value: 'PLAYWRIGHT_SLOWMO=400 make ui-tests-pw-show' },
      { label: 'HTML report', value: 'PLAYWRIGHT_REPORTER=html make ui-test && cd dashboard && npx playwright show-report' },
    ],
  },
  {
    title: 'Gateway Testing',
    description: 'Run backend suites to verify plugins and LiteLLM proxies.',
    commands: [
      { label: 'Run all pytest suites', value: 'pytest' },
      { label: 'E2E gateway smoke', value: 'pytest tests/test_end_to_end.py -q' },
    ],
  },
];

const CONFIG_FILES = [
  {
    title: 'Gateway Configuration',
    items: [
      {
        name: 'config/plugins.yaml',
        description: 'Enable or disable plugins, configure cache/db paths, and tweak proxy settings.',
      },
      {
        name: 'docs/project/PROJECT_STATUS.md',
        description: 'Living status document tracking risks, guard-rail reviews, and near-term goals.',
      },
    ],
  },
  {
    title: 'Dashboard & Testing',
    items: [
      {
        name: 'dashboard/playwright.config.js',
        description: 'Playwright defaults including base URL, reporters, and slow motion overrides.',
      },
      {
        name: 'dashboard/docs/TROUBLESHOOTING.md',
        description: 'Platform-specific fixes for WebKit dependencies and Playwright CLI tips.',
      },
    ],
  },
];

const ENVIRONMENT_HINTS = [
  {
    label: 'PLAYWRIGHT_WEB_SERVER',
    description: 'When set to `true`, the UI tests spawn `npm run dev` automatically before executing specs.',
  },
  {
    label: 'PLAYWRIGHT_SLOWMO / PLAYWRIGHT_SLOW_MO',
    description: 'Controls slow motion (ms) for headed Playwright runs. Defaults to 200ms in make targets.',
  },
  {
    label: 'PLAYWRIGHT_TEST_TIMEOUT',
    description: 'Overrides the per-test timeout (ms) in the Playwright config.',
  },
  {
    label: 'PLAYWRIGHT_REPORTER',
    description: 'Comma separated reporters (e.g. `list,html`) for custom output formats.',
  },
];

function Settings() {
  const [status, setStatus] = useState({ state: 'checking', detail: 'Checking gateway health…' });

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const res = await fetch(`${GATEWAY_URL}/health`);
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`);
        }
        const data = await res.json();
        if (data.status === 'healthy') {
          setStatus({ state: 'online', detail: `${data.service} v${data.version}` });
        } else {
          setStatus({ state: 'warning', detail: 'Gateway responded but status unknown' });
        }
      } catch (error) {
        console.error('Gateway health failed', error);
        setStatus({ state: 'offline', detail: 'Gateway unreachable' });
      }
    };
    fetchHealth();
  }, []);

  const handleCopy = async (value) => {
    try {
      await navigator.clipboard.writeText(value);
    } catch (error) {
      console.error('Copy failed', error);
    }
  };

  return (
    <div className="settings-page">
      <header className="settings-header">
        <div>
          <h1>⚙️ Gateway Settings & Tooling</h1>
          <p className="settings-subtitle">
            Reference environment status, frequently used commands, and configuration entry points.
          </p>
        </div>
        <div className={`settings-health settings-health-${status.state}`}>
          <span className="dot" />
          <span>{status.detail}</span>
        </div>
      </header>

      <section className="settings-grid">
        <article className="settings-card endpoints-card">
          <h2>Service Endpoints</h2>
          <ul>
            <li>
              <span className="label">Gateway REST</span>
              <code>{`${GATEWAY_URL}`}</code>
            </li>
            <li>
              <span className="label">Playground UI</span>
              <code>http://localhost:3000</code>
            </li>
            <li>
              <span className="label">OpenAI-compatible endpoint</span>
              <code>{`${GATEWAY_URL}/v1/chat/completions`}</code>
            </li>
          </ul>
        </article>

        <article className="settings-card env-card">
          <h2>Key Environment Variables</h2>
          <p className="section-description">
            These toggles influence the behaviour of UI tests and local developer flows.
          </p>
          <ul className="env-list">
            {ENVIRONMENT_HINTS.map((hint) => (
              <li key={hint.label}>
                <code>{hint.label}</code>
                <span>{hint.description}</span>
              </li>
            ))}
          </ul>
        </article>

        {COMMAND_SECTIONS.map((section) => (
          <article className="settings-card" key={section.title}>
            <h2>{section.title}</h2>
            <p className="section-description">{section.description}</p>
            <ul className="command-list">
              {section.commands.map((command) => (
                <li key={`${section.title}-${command.label}`}>
                  <div className="command-label">{command.label}</div>
                  <code>{command.value}</code>
                  <button type="button" className="command-copy" onClick={() => handleCopy(command.value)}>
                    Copy
                  </button>
                </li>
              ))}
            </ul>
          </article>
        ))}

        {CONFIG_FILES.map((group) => (
          <article className="settings-card" key={group.title}>
            <h2>{group.title}</h2>
            <ul className="file-list">
              {group.items.map((file) => (
                <li key={file.name}>
                  <code>{file.name}</code>
                  <p>{file.description}</p>
                </li>
              ))}
            </ul>
          </article>
        ))}

        <article className="settings-card note-card">
          <h2>Playground CLI Panel</h2>
          <p>
            The Playground page now mirrors the OpenAI-compatible payload the gateway receives. Use the curl preview and JSON
            copy buttons to integrate with scripts or share reproducible requests with teammates.
          </p>
          <p>
            Remember that the gateway normalises parameters per model. The preview helps verify the final payload before it
            hits the plugin pipeline.
          </p>
        </article>
      </section>
    </div>
  );
}

export default Settings;
