import { expect, test, type Page } from '@playwright/test';

const appPath = (path: string) => new URL(
  path,
  process.env.E2E_BASE_URL || `http://127.0.0.1:${process.env.E2E_PORT || '8000'}`,
).toString();
const waitForApi = (page: Page, path: string, method: string) => page.waitForResponse(response => {
  const url = new URL(response.url());
  return url.pathname === `/api/${path}` && response.request().method() === method;
});

async function login(page: Page, email: string, password: string) {
  await page.goto(appPath('/login'));
  const loginResponse = waitForApi(page, 'auth/login/', 'POST');
  await page.getByTestId('input-account-email').fill(email);
  await page.getByTestId('input-account-password').fill(password);
  await page.getByTestId('button-login').click();
  const response = await loginResponse;
  expect(response.status(), 'login API response').toBe(200);
  // Login redirects verified demo accounts to their role-specific home page;
  // the inbox prompt is only for unverified accounts.
  await expect(page.getByTestId('label-current-user')).toBeVisible();
}

test('visitor, candidate, and recruiter complete an application flow in isolated browser contexts', async ({ browser }) => {
  const visitorContext = await browser.newContext();
  const candidateContext = await browser.newContext();
  const recruiterContext = await browser.newContext();
  const contexts = [visitorContext, candidateContext, recruiterContext];
  try {
    const visitor = await visitorContext.newPage();
    const jobsResponse = waitForApi(visitor, 'jobs/', 'GET');
    await visitor.goto(appPath('/'));
    expect((await jobsResponse).status(), 'public jobs API response').toBe(200);
    await expect(visitor.getByTestId('card-job-job-platform')).toBeVisible();
    await visitor.getByTestId('link-job-job-platform').click();
    await expect(visitor.getByTestId('text-job-title')).toHaveText('Platform Engineer');
    await expect(visitor.getByTestId('button-open-application')).toBeVisible();
    expect(await visitor.evaluate(() => sessionStorage.getItem('steadwork.access_token'))).toBeNull();

    const candidate = await candidateContext.newPage();
    await login(
      candidate,
      process.env.E2E_CANDIDATE_EMAIL!,
      process.env.E2E_CANDIDATE_PASSWORD!,
    );
    expect(await candidate.evaluate(() => sessionStorage.getItem('steadwork.access_token'))).toBeTruthy();

    await candidate.goto(appPath('/employer/jobs/job-platform/applicants'));
    await expect(candidate.getByRole('heading', { name: 'You do not have access to this page' })).toBeVisible();
    await expect(candidate.getByText('This area is for hiring team accounts.')).toBeVisible();
    await expect(candidate.getByTestId(/^row-applicant-/)).toHaveCount(0);

    await candidate.goto(appPath('/profile'));
    await expect(candidate.getByRole('heading', { name: 'A profile that grows with you' })).toBeVisible();
    await candidate.getByTestId('input-add-cv').setInputFiles({
      name: 'candidate-e2e.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('%PDF-1.4 E2E resume filename fixture'),
    });
    await expect(candidate.getByRole('status')).toContainText('Added candidate-e2e.pdf');

    await candidate.goto(appPath('/jobs/job-platform'));
    await expect(candidate.getByTestId('button-open-application')).toBeVisible();
    await candidate.getByTestId('button-open-application').click();
    const dialog = candidate.getByRole('dialog');
    await expect(dialog).toBeVisible();
    await dialog.getByTestId('input-applicant-name').fill('E2E Candidate');
    await dialog.getByTestId('input-applicant-email').fill(process.env.E2E_CANDIDATE_EMAIL!);
    await expect(dialog.getByTestId('select-cv')).toHaveValue('candidate-e2e.pdf');
    const applicationResponse = waitForApi(candidate, 'applications/', 'POST');
    await dialog.getByTestId('button-submit-application').click();
    const created = await applicationResponse;
    expect(created.status(), 'application API response').toBe(201);
    const application = await created.json() as { id: string; status: string };
    expect(application.status).toBe('Applied');
    await expect(candidate.getByTestId('status-application-feedback')).toContainText('Your application is in.');

    const applicationsResponse = waitForApi(candidate, 'candidate/applications/', 'GET');
    await candidate.goto(appPath('/applications'));
    expect((await applicationsResponse).status(), 'candidate applications API response').toBe(200);
    const candidateRow = candidate.getByTestId(`row-application-${application.id}`);
    await expect(candidateRow).toBeVisible();
    await expect(candidate.getByTestId(`status-application-${application.id}`)).toHaveText('Applied');

    const recruiter = await recruiterContext.newPage();
    await login(
      recruiter,
      process.env.E2E_RECRUITER_EMAIL!,
      process.env.E2E_RECRUITER_PASSWORD!,
    );
    expect(await recruiter.evaluate(() => sessionStorage.getItem('steadwork.access_token'))).toBeTruthy();
    await recruiter.goto(appPath('/employer'));
    const applicantsResponsePromise = recruiter.waitForResponse(response => {
      const url = new URL(response.url());
      return url.pathname === '/api/employer/jobs/job-platform/applications/'
        && response.request().method() === 'GET';
    });
    await recruiter.getByTestId('link-applicants-job-platform').click();
    const applicantsResponse = await applicantsResponsePromise;
    expect(applicantsResponse.status(), 'recruiter applicants API response').toBe(200);
    const applicant = recruiter.getByTestId(`row-applicant-${application.id}`);
    await expect(applicant).toBeVisible();
    const statusResponse = waitForApi(recruiter, `employer/applications/${application.id}/status/`, 'POST');
    await applicant.getByLabel('Update status for E2E Candidate').selectOption('Under Review');
    expect((await statusResponse).status(), 'recruiter status API response').toBe(200);
    await expect(applicant).toContainText('Under Review');

    const refreshedApplications = waitForApi(candidate, 'candidate/applications/', 'GET');
    await candidate.reload();
    expect((await refreshedApplications).status(), 'refreshed candidate applications response').toBe(200);
    await expect(candidate.getByTestId(`status-application-${application.id}`)).toHaveText('Under Review');
    expect(await visitor.evaluate(() => sessionStorage.getItem('steadwork.access_token'))).toBeNull();
    expect(await candidate.evaluate(() => sessionStorage.getItem('steadwork.access_token')))
      .not.toBe(await recruiter.evaluate(() => sessionStorage.getItem('steadwork.access_token')));
  } finally {
    await Promise.all(contexts.map(context => context.close()));
  }
});
