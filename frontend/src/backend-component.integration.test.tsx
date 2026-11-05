import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterAll, beforeAll, beforeEach, describe, expect, it } from 'vitest';
import { spawn, type ChildProcess } from 'node:child_process';
import { createServer } from 'node:net';
import path from 'node:path';
import { setTimeout as sleep } from 'node:timers/promises';
import App from './App';
import { ACCESS_TOKEN_KEY } from './services/session';

const originalFetch = globalThis.fetch;
globalThis.IS_REACT_ACT_ENVIRONMENT = true;
let backend: ChildProcess;
let vite: ChildProcess;
let backendPort: number;
let vitePort: number;
let root: Root;
let container: HTMLDivElement;
let serviceExitError: Error | undefined;
let stopping = false;
const backendUrl = () => `http://127.0.0.1:${backendPort}`;

const freePort = async () => new Promise<number>((resolve, reject) => {
  const server = createServer();
  server.once('error', reject);
  server.listen(0, '127.0.0.1', () => {
    const address = server.address();
    const port = typeof address === 'object' && address ? address.port : 0;
    server.close(() => resolve(port));
  });
});

const waitFor = async (check: () => boolean | Promise<boolean>, timeout = 10_000) => {
  const started = Date.now();
  while (true) {
    let matched = false;
    await act(async () => {
      matched = await check();
      if (!matched) await sleep(50);
    });
    if (matched) return;
    if (serviceExitError) throw serviceExitError;
    if (Date.now() - started > timeout) throw new Error('Timed out waiting for UI state.');
  }
};

const start = (command: string, args: string[], cwd: string, env: Record<string, string>) => {
  serviceExitError = undefined;
  const child = spawn(command, args, { cwd, env: { ...process.env, ...env }, detached: true, stdio: 'ignore' });
  child.once('error', error => { throw error; });
  child.once('exit', code => {
    if (!stopping && code !== null && code !== 0) serviceExitError = new Error(`Service exited unexpectedly with status ${code}.`);
  });
  return child;
};

const stopGroup = async (child: ChildProcess | undefined) => {
  if (!child || child.exitCode !== null) return;
  await new Promise<void>((resolve, reject) => {
    const finish = () => { child.removeListener('error', reject); resolve(); };
    child.once('exit', finish);
    child.once('error', reject);
    if (child.pid) {
      try { process.kill(-child.pid, 'SIGTERM'); } catch (error) {
        if ((error as NodeJS.ErrnoException).code === 'ESRCH') finish();
        else reject(error);
      }
    } else finish();
  });
};

const button = (testId: string) => document.querySelector<HTMLButtonElement>(`[data-testid="${testId}"]`)!;
const click = async (element: Element) => { await act(async () => { element.dispatchEvent(new MouseEvent('click', { bubbles: true })); }); };
const input = (testId: string, value: string) => {
  const element = document.querySelector<HTMLInputElement | HTMLTextAreaElement>(`[data-testid="${testId}"]`)!;
  const prototype = element instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
  const setter = Object.getOwnPropertyDescriptor(prototype, 'value')!.set!;
  act(() => {
    setter.call(element, value);
    element.dispatchEvent(new Event('input', { bubbles: true }));
    element.dispatchEvent(new Event('change', { bubbles: true }));
  });
  return element;
};
const submit = async (form: HTMLFormElement) => {
  await act(async () => { form.dispatchEvent(new SubmitEvent('submit', { bubbles: true, cancelable: true })); });
};
const login = async (email: string, password: string) => {
  if (!document.querySelector('[data-testid="link-sign-in"]') && document.querySelector('[data-testid="button-sign-out"]')) {
    await click(document.querySelector('[data-testid="button-sign-out"]')!);
    await waitFor(() => Boolean(document.querySelector('[data-testid="link-sign-in"]')));
  }
  await click(document.querySelector('[data-testid="link-sign-in"]')!);
  await waitFor(() => Boolean(document.querySelector('[data-testid="button-login"]')));
  input('input-account-email', email);
  input('input-account-password', password);
  await submit(document.querySelector('form')!);
  await waitFor(() => !document.querySelector('[data-testid="button-login"]'));
  if (document.querySelector('[data-testid="button-demo-verify-email"]')) {
    window.history.pushState({}, '', '/');
    await act(async () => { window.dispatchEvent(new PopStateEvent('popstate')); });
  }
  await waitFor(() => Boolean(document.querySelector('[data-testid="link-job-job-platform"]') || document.querySelector('[data-testid="button-create-job"]')));
};

beforeAll(async () => {
  backendPort = await freePort();
  vitePort = await freePort();
  const rootDir = process.cwd();
  const backendDir = path.resolve(rootDir, '../backend');
  backend = start(path.join(backendDir, '.venv/bin/python'), ['manage.py', 'runserver', `127.0.0.1:${backendPort}`], backendDir, {
    STEADWORK_TEST_CLEAN_APPLICATIONS: '1',
    STEADWORK_STORE: 'inmemory',
  });
  await waitFor(async () => {
    try { return (await originalFetch(`${backendUrl()}/api/health/`)).ok; } catch { return false; }
  });

  vite = start('npm', ['run', 'dev', '--', '--host', '127.0.0.1', '--port', String(vitePort)], rootDir, {
    API_PROXY_TARGET: backendUrl(),
  });
  await waitFor(async () => {
    try { return (await originalFetch(`http://127.0.0.1:${vitePort}/`)).ok; } catch { return false; }
  });
  globalThis.fetch = (inputValue, init) => originalFetch(
    typeof inputValue === 'string' && inputValue.startsWith('/') ? `http://127.0.0.1:${vitePort}${inputValue}` : inputValue,
    init,
  );
});

const resetBackend = async () => {
  await stopGroup(backend);
  const backendDir = path.resolve(process.cwd(), '../backend');
  backend = start(path.join(backendDir, '.venv/bin/python'), ['manage.py', 'runserver', `127.0.0.1:${backendPort}`], backendDir, {
    STEADWORK_TEST_CLEAN_APPLICATIONS: '1',
    STEADWORK_STORE: 'inmemory',
  });
  await waitFor(async () => { try { return (await originalFetch(`${backendUrl()}/api/health/`)).ok; } catch { return false; } });
};

afterAll(async () => {
  stopping = true;
  globalThis.fetch = originalFetch;
  await act(async () => { root?.unmount(); });
  await Promise.all([stopGroup(vite), stopGroup(backend)]);
});

beforeEach(async () => {
  if (root) await act(async () => { root.unmount(); });
  await resetBackend();
  window.sessionStorage.clear();
  window.localStorage.clear();
  window.history.pushState({}, '', '/');
  container = document.createElement('div');
  document.body.replaceChildren(container);
  root = createRoot(container);
  await act(async () => { root.render(<App />); });
  await waitFor(() => Boolean(document.querySelector('[data-testid="card-job-job-platform"]')));
});

describe('frontend journeys over the live API and Vite proxy', () => {
  it('submits account registration to the live API and signs in immediately', async () => {
    await click(document.querySelector('[data-testid="link-create-account"]')!);
    await waitFor(() => Boolean(document.querySelector('[data-testid="button-register"]')));
    input('input-account-name', 'New E2E Candidate');
    input('input-account-email', 'new-e2e-candidate@example.com');
    input('input-account-password', 'candidate-password-123');
    await submit(document.querySelector('form')!);
    await waitFor(() => document.querySelector('[data-testid="label-current-user"]')?.textContent === 'New E2E Candidate');
    expect(window.sessionStorage.getItem(ACCESS_TOKEN_KEY)).toBeTruthy();
    expect(document.querySelector('[data-testid="status-auth-error"]')).toBeNull();
  });

  it('shows a sign-in prompt instead of calling protected application pages signed out', async () => {
    await click(document.querySelector('[data-testid="nav-applications"]')!);
    await waitFor(() => Boolean(document.querySelector('[data-testid="link-protected-sign-in"]')));
    expect(document.body.textContent).toContain('Sign in to continue');
    expect(document.querySelector<HTMLAnchorElement>('[data-testid="link-protected-sign-in"]')?.getAttribute('href')).toContain('returnTo');
    await click(document.querySelector('[data-testid="nav-my-profile"]')!);
    await waitFor(() => Boolean(document.querySelector('[data-testid="link-protected-sign-in"]')));
    expect(document.querySelector('[aria-label="Checking your session"]')).toBeNull();
  });

  it('blocks a signed-in candidate from employer pages with a role-specific state', async () => {
    await login('candidate@example.com', 'candidate-password');
    window.history.pushState({}, '', '/employer');
    await act(async () => { window.dispatchEvent(new PopStateEvent('popstate')); });
    await waitFor(() => document.body.textContent?.includes('You do not have access to this page') ?? false);
    expect(document.body.textContent).toContain('hiring team accounts');
  });

  it('loads public jobs and company details, then shows an actionable invalid request', async () => {
    expect(document.body.textContent).toContain('Platform Engineer');
    await click(document.querySelector('[data-testid="link-job-job-platform"]')!);
    await waitFor(() => Boolean(document.querySelector('[data-testid="text-job-title"]')));
    expect(document.body.textContent).toContain('Platform Engineer');
    await waitFor(() => document.body.textContent?.includes('Acme Technologies') ?? false);
    expect(document.body.textContent).toContain('Acme Technologies');
    await click(button('button-detail-save'));
    await waitFor(() => Boolean(document.querySelector('[data-testid="link-sign-in"]')));
    expect(document.body.textContent).toContain('Sign in');
  });

  it('authenticates a candidate, saves, applies, lists and withdraws a job', async () => {
    await login('candidate@example.com', 'candidate-password');
    await click(document.querySelector('[data-testid="link-job-job-platform"]')!);
    await waitFor(() => Boolean(document.querySelector('[data-testid="button-detail-save"]')));
    await click(button('button-detail-save'));
    await waitFor(() => document.body.textContent?.includes('Saved') ?? false);
    await waitFor(() => !button('button-open-application').disabled);
    await click(button('button-open-application'));
    await waitFor(() => Boolean(document.querySelector('[data-testid="button-submit-application"]')));
    input('input-applicant-name', 'Candidate');
    input('input-applicant-email', 'candidate@example.com');
    input('input-cover-letter', 'A thoughtful application.');
    input('select-cv', 'Candidate-Resume.pdf');
    await submit(document.querySelector('[role="dialog"] form')!);
    await waitFor(() => Boolean(document.body.textContent?.includes('Your application is in') || document.querySelector('[data-testid="status-application-error"]')));
    expect(document.querySelector('[data-testid="status-application-feedback"]')?.textContent, document.querySelector('[data-testid="status-application-error"]')?.textContent).toContain('Your application is in');
    await click(document.querySelector('[data-testid="nav-applications"]')!);
    await waitFor(() => Boolean(document.querySelector('[data-testid^="row-application-"]')));
    const withdraw = document.querySelector<HTMLButtonElement>('[data-testid^="button-withdraw-"]')!;
    await click(withdraw);
    await waitFor(() => Boolean(document.querySelector('[data-testid^="button-confirm-withdraw-"]')));
    await click(document.querySelector('[data-testid^="button-confirm-withdraw-"]')!);
    await waitFor(() => document.body.textContent?.includes('Withdrawn') ?? false);
  });

  it('lets an employer review the candidate application and update status', async () => {
    await login('candidate@example.com', 'candidate-password');
    await click(document.querySelector('[data-testid="link-job-job-platform"]')!);
    await waitFor(() => Boolean(document.querySelector('[data-testid="button-detail-save"]')));
    await waitFor(() => !button('button-open-application').disabled);
    await click(button('button-open-application'));
    await waitFor(() => Boolean(document.querySelector('[data-testid="button-submit-application"]')));
    input('input-applicant-name', 'Candidate');
    input('input-applicant-email', 'candidate@example.com');
    input('input-cover-letter', 'Please consider me.');
    input('select-cv', 'Candidate-Resume.pdf');
    await submit(document.querySelector('[role="dialog"] form')!);
    await waitFor(() => Boolean(document.body.textContent?.includes('Your application is in') || document.querySelector('[data-testid="status-application-error"]')));
    expect(document.querySelector('[data-testid="status-application-feedback"]')?.textContent, document.querySelector('[data-testid="status-application-error"]')?.textContent).toContain('Your application is in');
    await login('recruiter@example.com', 'recruiter-password');
    window.history.pushState({}, '', '/employer/jobs/job-platform/applicants');
    await act(async () => { window.dispatchEvent(new PopStateEvent('popstate')); });
    await waitFor(() => Boolean(document.querySelector('[data-testid^="row-applicant-"]')));
    const status = document.querySelector<HTMLSelectElement>('[data-testid^="select-applicant-status-"]')!;
    status.value = 'Under Review';
    await act(async () => { status.dispatchEvent(new Event('change', { bubbles: true })); });
    await waitFor(() => document.body.textContent?.includes('marked Under Review') ?? false);
    expect(window.sessionStorage.getItem(ACCESS_TOKEN_KEY)).toBeTruthy();
  }, 30_000);
});
