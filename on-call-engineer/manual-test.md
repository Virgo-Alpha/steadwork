# Manual on-call agent test

This test uses the real configured headless provider and local Grafana. It injects one narrow application failure on a disposable GitHub branch, lets the firing alert wake the agent, and verifies the agent's tested correction. **Do not run the injected fault on `main`.**

## Important limitation

The CI workflow runs only for pushes to `main`; a push to `oncall-agent-manual-test` runs neither CI nor the development deployment. The existing runner can target this branch with `ONCALL_MAIN_BRANCH`, but it still waits for a CI run and development deployment after pushing. Since neither occurs on this branch, it will wait up to an hour and then record an escalation. After the audit records `code_pushed`, stop the poller with Ctrl+C. This leaves a clear audit record and the fix commit on the test branch, but no `recovery_confirmed` record. You will verify local recovery yourself after pulling the fix. This test therefore demonstrates alert wake-up, investigation, correction, backend tests, and branch push; it does not test the runner's automated deployment/recovery completion.

## Default headless Codex adapter

The poller uses the bundled [Codex adapter](adapters/codex.py) when `ONCALL_AGENT_COMMAND` is unset. It starts a separate headless `codex exec` process for each alert and requests the runner's structured result format. By default, Codex can write within the incident checkout using the `workspace-write` sandbox. This is a new CLI run, not the currently open Codex chat session. The Codex CLI must be installed on `PATH` and authenticated on this computer; if needed, sign in once with `codex login`. The adapter uses that saved CLI login, so you do not need to set a provider command, provider/model labels, API key, or environment allowlist for the default setup. Codex chooses its configured default model.

Before starting the poller, confirm that the CLI is available:

```sh
command -v codex
```

### Linux hosts that block user namespaces

Codex's Linux `workspace-write` sandbox uses Bubblewrap. If `unshare -Ur true` fails with `Operation not permitted`, this host blocks the user namespaces Bubblewrap needs; the agent will escalate without changing code. The preferred solution is to run the test in a disposable VM or Linux environment that permits the sandbox.

For this local acceptance test only, you can opt into Codex's unrestricted mode by exporting this in the same terminal that starts the poller:

```sh
export ONCALL_CODEX_SANDBOX=danger-full-access
```

This disables Codex's filesystem and network sandbox. The adapter invokes non-interactive `codex exec` without an approval flag, so the run does not pause for permission prompts. The agent can access files, credentials, and network available to your operating-system account. A test Git branch does not isolate your computer. Use a disposable OS account or VM if possible, and do not leave this mode enabled after testing. Codex documents `danger-full-access` for controlled environments only: [CLI non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode).

When the manual test is finished, return to the default sandbox in that terminal:

```sh
unset ONCALL_CODEX_SANDBOX
```

If you previously exported a placeholder or custom `ONCALL_AGENT_COMMAND`, clear it in the poller's terminal so the bundled Codex default is selected:

```sh
unset ONCALL_AGENT_COMMAND
```

Optional: pin a Codex model. This also records the selected model in the audit:

```sh
export ONCALL_AGENT_MODEL='<codex-model-id>'
```

To use another provider, set `ONCALL_AGENT_COMMAND` to an adapter implementing the [provider contract](README.md#provider-adapter-contract). Provider credentials are passed only when explicitly named in `ONCALL_AGENT_ENV_ALLOWLIST`. Do not put credentials in repository files.

### Retry after the missing-adapter escalation

The previous run is recorded as `escalated` for the alert fingerprint in `on-call-engineer/state/manual-test/runner-state.json`. While that fingerprint remains active, the poller deduplicates it and will not retry it from the same state directory. Stop the old poller, make sure the Codex CLI is installed and signed in, then use a new state directory. This preserves the previous audit rather than deleting it. The alert must still be **Firing**; if it has resolved, send the three fault-triggering curl requests again and wait for it to fire.

## 1. Create the test branch

First ensure the on-call implementation is committed and present on the base branch you plan to use. From that clean checkout, create the dedicated branch and push it:

```sh
git switch -c oncall-agent-manual-test
git push -u origin oncall-agent-manual-test
```

If you already created the remote branch, check it out instead:

```sh
git fetch origin
git switch --track origin/oncall-agent-manual-test
```

The branch must contain the runner, provider prompt, and this guide. Keep the worktree clean before starting the poller. Branch pushes do not match the workflow's `push: branches: [main]` filter, so they do not run CI or deploy to development.

## 2. Add and publish the controlled fault

In `backend/api/routers.py`, find `create_guest_application`. After the input and job validation and before the duplicate-application check, add:

```python
# ONCALL_TEST_INJECTED_FAULT: local on-call acceptance test only.
if values["candidateEmail"].endswith("@oncall-test.invalid"):
    raise RuntimeError("simulated on-call application failure")
```

Commit and push this setup fault on the test branch so the agent's remote checkout can reproduce it:

```sh
git add backend/api/routers.py
git commit -m "test(oncall): inject guest application failure"
git push
```

The fault only affects reserved test addresses. The agent prompt instructs the agent to comment out this marked block, explain why it is disabled, and leave the code in place. Start Steadwork and its local observability stack from this checkout:

```sh
make run
```

## 3. Start the poller on the test branch

After installing and authenticating the Codex CLI, use another terminal at the repository root and run:

```sh
export ONCALL_MAIN_BRANCH=oncall-agent-manual-test
export ONCALL_STATE_DIR="$PWD/on-call-engineer/state/manual-test-retry-3"
python3 on-call-engineer/poll.py
```

`ONCALL_MAIN_BRANCH` tells the existing runner which branch to clone and push. Use a different `ONCALL_STATE_DIR` name for each retry. No `ONCALL_AGENT_COMMAND` export is needed for the bundled Codex adapter. If Codex is missing or unauthenticated, the run will record an escalation; inspect that run's `agent.stderr` and audit events for the startup error.

The poller checks Grafana once a minute. Keep this terminal open.

<img width="1329" height="294" alt="Screenshot from 2026-11-07 23-59-07" src="https://github.com/user-attachments/assets/eaaede5f-be32-43dc-9193-3e766119cede" />

## 4. Trigger the operational alert with curl

Submit three guest applications with distinct test emails. `job-platform` is included in the local demo data:

```sh
for n in 1 2 3; do
  curl -i http://127.0.0.1:8000/api/applications/guest/ \
    -H 'Content-Type: application/json' \
    -d "{\"jobId\":\"job-platform\",\"candidateName\":\"On-call Test\",\"candidateEmail\":\"oncall-test-${n}@oncall-test.invalid\",\"cvName\":\"test.pdf\",\"coverLetter\":\"\"}"
done
```

Each request should return HTTP 500 and produce a `submit_application` / `server_error` telemetry event.

<img width="1521" height="735" alt="Screenshot from 2026-11-07 22-45-47" src="https://github.com/user-attachments/assets/d8dab00f-40c1-4462-b812-f09afe09c022" />

## 5. Observe the agent working

In Grafana, open **Alerting → Alert rules → Repeated application submission failures**. The alert requires at least three failures in ten minutes and a five-minute firing period, with one-minute rule evaluation. Wait for **Pending** to become **Firing**. The poller should notice it within its next one-minute poll.

On the Steadwork overview dashboard, check **User actions by outcome** for `submit_application · server_error` and **Recent user-action logs** for `user_action_failed` records with trace and span IDs.

In a third terminal, follow the audit trail:

```sh
tail -F on-call-engineer/state/manual-test-retry-1/audit.jsonl
```

<img width="1859" height="731" alt="Screenshot from 2026-11-08 00-00-30" src="https://github.com/user-attachments/assets/8e508b74-6db6-46eb-8d72-3b769a695fc0" />

The evidence that the agent woke and investigated is the sequence `alert_observed`, `context_collected`, `investigation_started`, and `investigation_completed`, including the alert fingerprint and cited telemetry. The run directory recorded in the audit contains `incident.json`, `agent.stdout`, `agent.stderr`, and `backend-tests.log`. The final test evidence is a `code_pushed` record containing the commit SHA and `test_result: passed`; the fix commit should appear on `oncall-agent-manual-test` in GitHub.

**When `code_pushed` appears, press Ctrl+C in the poller terminal.** It will otherwise wait for a CI/development deployment that this branch does not trigger, then record an escalation. Do not interpret that expected wait-timeout escalation as a failed agent fix; the audit's `code_pushed` event and passing backend test log are the evidence for the agent response.

## 6. Apply the fix locally and verify recovery

In the repository terminal, fast-forward your test checkout to the agent's branch commit:

```sh
git pull --ff-only origin oncall-agent-manual-test
```

The local Django development server should reload the updated file. Confirm the marked fault is still present but commented out with the agent's explanation. Run the curl loop again with fresh addresses; requests should now return HTTP 201:

```sh
for n in 1 2 3; do
  curl -i http://127.0.0.1:8000/api/applications/guest/ \
    -H 'Content-Type: application/json' \
    -d "{\"jobId\":\"job-platform\",\"candidateName\":\"On-call Test\",\"candidateEmail\":\"oncall-fixed-${n}@oncall-test.invalid\",\"cvName\":\"test.pdf\",\"coverLetter\":\"\"}"
done
```

Grafana's ten-minute error window can retain the old failures after the fix. Allow about 10–12 minutes after the last failing request for the metric to clear and the alert to resolve. Confirm no new `server_error` outcomes appear, the alert shows **Resolved**, and health remains available at <http://127.0.0.1:8000/api/health/>.

Capture the **Firing** alert, the audit's investigation and `code_pushed` entries, the passing backend test log, the GitHub branch commit, the commented fault, successful post-fix curl responses, and the **Resolved** alert. Stop `make run` when finished. Keep or delete the test branch after reviewing it; do not merge it to `main` as part of this test.
