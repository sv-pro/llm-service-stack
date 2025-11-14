// API Configuration
// In production (Render), VITE_API_URL will be set automatically
// In development, it falls back to localhost
function readQueryOverride() {
  if (typeof window === 'undefined') {
    return null;
  }

  const params = new URLSearchParams(window.location.search);
  const override = params.get('gateway');
  if (override) {
    try {
      const url = new URL(override);
      localStorage.setItem('gateway:override', url.toString());
      return url.toString();
    } catch {
      console.warn('[GatewayConfig] Ignoring invalid gateway query override:', override);
    }
  }

  const stored = localStorage.getItem('gateway:override');
  return stored || null;
}

const LOOPBACK_HOSTS = new Set(['0.0.0.0', '127.0.0.1', 'localhost']);

function stripTrailingSlash(url) {
  return url ? url.replace(/\/$/, '') : url;
}

function inferApiBase() {
  const manual = readQueryOverride();
  if (manual) {
    return stripTrailingSlash(manual);
  }

  if (typeof window === 'undefined') {
    return 'http://localhost:8000';
  }

  const { protocol, hostname, port } = window.location;

  // Local development
  if (LOOPBACK_HOSTS.has(hostname)) {
    const targetPort = port && port !== '3000' ? port : '8000';
    const normalizedHost = hostname === '0.0.0.0' ? '127.0.0.1' : hostname;
    return `${protocol}//${normalizedHost}:${targetPort}`;
  }

  // Codespaces style: https://workspace-3000.app.github.dev
  if (hostname.includes('-3000')) {
    return `${protocol}//${hostname.replace('-3000', '-8000')}`;
  }

  // Gitpod / Okteto style: https://3000-workspace.gitpod.io
  if (hostname.startsWith('3000-')) {
    return `${protocol}//${hostname.replace('3000-', '8000-')}`;
  }

  // Generic fallback: same host, switch port to 8000 if empty
  if (!port || port === '3000') {
    return `${protocol}//${hostname}:8000`;
  }

  return `${protocol}//${hostname}:${port}`;
}

function resolveConfiguredBase() {
  const configured = import.meta.env.VITE_API_URL;
  if (!configured) {
    return null;
  }

  try {
    const parsed = new URL(configured);
    const isLoopback = LOOPBACK_HOSTS.has(parsed.hostname);
    if (!isLoopback) {
      return stripTrailingSlash(parsed.toString());
    }
    return inferApiBase();
  } catch (err) {
    console.warn('[GatewayConfig] Could not parse VITE_API_URL, falling back to inference:', err);
    return stripTrailingSlash(configured);
  }

  return null;
}

const API_URL = resolveConfiguredBase() || inferApiBase();

export default API_URL;
