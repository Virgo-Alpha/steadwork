# Browser end-to-end tests

The Playwright suite exercises the public, candidate and recruiter job-board
flows through the frontend served by the root Docker Compose stack. It creates
a unique Compose project and database volume for each run, waits for the app
health check, and removes only that project and volume on success, test failure,
startup failure, or an interrupt handled by the runner.

Install the isolated test dependency and Chromium browser with `make e2e-install`
(or `make test-setup`). The E2E runner also checks for its pinned Chromium build
and installs it into the same cache if it is missing:

```sh
make e2e-install
```

The suite requires seeded local-only candidate and recruiter accounts. Provide
their values through the environment; the test source does not contain account
credentials:

```sh
export E2E_CANDIDATE_EMAIL='candidate@example.com'
export E2E_CANDIDATE_PASSWORD='candidate-password'
export E2E_RECRUITER_EMAIL='recruiter@example.com'
export E2E_RECRUITER_PASSWORD='recruiter-password'
npm test
```

These are local demo accounts, not production credentials. The runner generates
temporary PostgreSQL credentials, selects a per-run host port, and supplies a
test-only Compose override that leaves seeded jobs/users available but omits the
pre-seeded application so the candidate can perform the flow. CV attachment is
exercised through the UI; the app stores its filename only. No database queries
are made by the tests.
