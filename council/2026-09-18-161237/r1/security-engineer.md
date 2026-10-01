The fatal flaw is the combination, not the agent itself: an LLM with tools, a secret in its environment, attacker-controllable input and a public log. Remove any one of the four and the hole closes. So the agent never runs on `pull_request`, never on `pull_request_target`, and never holds a write token.

**Triggers allowed to see the secret**
- The secret is exposed on `schedule` (weekly) and `workflow_dispatch` only, in a new `audit.yaml`. It does not go in `ci.yaml`, whose `pull_request` trigger must stay secret-free.
- The job reuses the guard the `remember` job already has: `if: github.repository == 'anpawo/Video-Code'`.
- Fork PRs keep getting the deterministic `repetition_check.py` and nothing else.
- `cd-mirror.yaml` already hands its deploy key to a `pull_request: opened` run. That exposure is small today and should not be copied.

**Permissions**
```yaml
permissions: {}
jobs:
  audit:
    permissions:
      contents: read
      issues: write   # one rolling issue, nothing else
```
- No `pull-requests: write`, no `id-token`, and never `contents: write`.
- Checkout uses `persist-credentials: false`, so no token sits in `.git/config` for a Bash tool to read.

**Two steps, with the secret in one of them**
- Step 1 runs the deterministic candidate generator and writes `candidates.json`.
- Step 2 is the only step with `ANTHROPIC_API_KEY` in its `env:`, following the `cd-mirror` rule of one step, one reader. The agent gets no `GH_TOKEN` at all.
- Step 3 is plain `gh issue edit`. It posts the agent's JSON after a schema check: fixed fields, length-capped, file paths must exist in the tree.
- The agent cannot write anywhere, and the step that writes runs no LLM.

**Tool allowlist**
- `--allowedTools "Read,Grep,Glob"`.
- Disallowed: `Bash`, `WebFetch`, `WebSearch`, `Edit`, `Write` and MCP. With no network tool and no shell, an injected comment in a source file has nowhere to send the key.
- `--max-turns 15` caps the run.

**Auth**
- A metered API key in a dedicated workspace with a $20 monthly spend cap.
- Not the subscription token: a leak of that lends out the owner's interactive quota for a year. A capped key leaks $20.
- The key lets us run `--bare`, which also stops the repo's own CLAUDE.md being loaded as instructions.

**Logs**
- `show_full_output` stays off. Only the validated JSON reaches the issue.

**Supply chain**
- Pin `anthropics/claude-code-action` by 40-character SHA, as `ci.yaml` does for `benchmark-action`.
- Better: `npm i -g @anthropic-ai/claude-code@<exact version>` and headless `claude -p`. That is one fewer third-party action near a secret.

**Write policy**
- The agent never pushes a branch. A bot that pushes to a repo with an unprotected main is one misconfigured ref away from pushing to main.
- It proposes changes in the issue; the owner applies them locally.

**Before the first run**
- Finish removing the two extra accounts that still hold push rights.
- Set the default workflow token to read-only in the repo settings.
