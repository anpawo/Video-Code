**Drop `pull_request` and `push` as agent triggers.** On a public repo, that alone removes the three documented risks: fork PRs never receive the secret, PR text never reaches the prompt, and the agent never reacts to untrusted input. The owner pushes straight to main, so nothing else is lost.

**Layout.** One new file, `.github/workflows/twins.yaml`. `ci.yaml` and `test/repetition_check.py` stay exactly as they are and remain the only gate.

- `on: schedule: cron '0 4 * * 1'`, an hour after Nightly's 03:00 cron. There is no `workflow_dispatch`. `nightly.yaml` already records why: a dispatched run executes the workflow file of the dispatched ref, and `main` is unprotected.
- `concurrency: {group: twins, cancel-in-progress: true}` and `timeout-minutes: 15`.
- Job `candidates` has `contents: read` and no secrets. It runs `python3 test/repetition_check.py`, then `npx jscpd@4.0.5 --max-lines 5000 --reporters json`. The `--max-lines` flag matters because jscpd's default silently skips the two largest files. The job uploads the JSON, and an empty clone list ends the run before any model call is made.
- Job `triage` has `needs: candidates`, `contents: read` and `issues: write`. It checks out the repo and runs headless `claude -p --output-format json --max-turns 25 --allowedTools "Read,Grep,Glob"` on a Sonnet-class model. The agent has no Bash, no Edit and no git credentials, so it can neither push nor publish a board.

**Auth.** Use an API key held in a GitHub Environment restricted to `main`, under a dedicated Anthropic workspace with a $10 monthly spend limit. The provider-side limit is the real cost cap because it still holds if the YAML is wrong. Do not use the subscription token: a CI job that competes with the owner's interactive 5-hour window will be switched off the first time it throttles him. The API key also permits `--bare`, which prevents CLAUDE.md's board-update order from being loaded. Expected bill is about $0.80 × 4 ≈ $4 a month.

**Output.** Maintain a single rolling issue labelled `twins`, found with `gh issue list --label twins` and rewritten each week with `gh issue edit --body-file`. It lists at most five findings and includes `total_cost_usd` from the run. Post only that parsed digest, because a raw transcript in the public Actions log leaks everything the model read. An empty week leaves the issue untouched and sends no notification.

**Failure at 3am.** The schedule run goes red and GitHub emails the owner. A failed run blocks no push.

**Known gap.** Weekly cadence means a new twin can sit undetected for up to seven days. The 1.2-second count ratchet covers that window. Running the agent on every push would cost about $100 a month to close a gap that is already covered.
