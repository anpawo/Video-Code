**Response A:**

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

**Response B:**

**"Still optimised" in CI can only mean one thing: a number exists for this code.** The gap in the repo today is a missing measurement, not a missing reviewer. The last row of `test/perf/history.jsonl` measures `96587a7`, dated 2026-09-06. Since then 25 commits have touched `src/`, `include/` or `assets/shaders/` with no new row. The guard exists, but nobody has run it in twelve days.

**The design has three parts, and only the third is an agent.**

- **Staleness check (deterministic, fast lane, red but non-blocking).** It counts commits touching `src/`, `include/` and `assets/shaders/` since the sha in the last history row. Past a limit of 10 it prints "N engine commits unmeasured — run `guard.py --record`". It takes about ten lines in `history.py` next to `--verify` and costs nothing. It claims nothing about speed.
- **`digest.py` stays as it is.** It is the only honest perf gate a shared runner can hold, and its zero tolerance stays.
- **Agent (weekly, advisory, candidates-first, the same run as the duplication audit).** It reads only the engine diff since the last measured sha. It may flag four kinds of change, each with a file and line:
  - work that moved from per-scene to per-frame, or from per-frame to per-object;
  - a heap allocation, string build or container copy inside a draw or bake loop;
  - Vulkan resources created or pipelines rebuilt per frame;
  - a loop nested inside another loop over the same collection.

**Every agent finding is a question that ends in the command that answers it.** The agent may write "this adds an allocation per glyph per frame; `stress_text.py` would show it; measure". It must never write "slow", "faster", a percentage, an estimated millisecond figure or a fix.

`guard.py` already documents that wall time on identical code swings 2–4% at rest, and that a ±20% gate fired on 26.8% of clean runs. An LLM reading a diff has less signal than that, because it has no clock at all. If the agent cannot name the loop and its trip count, it stays silent.

**Two things are not built.**

- There is no CI timing step and no "perf score" at any tolerance.
- The agent does not review the Python library for micro-optimisations. `digest.py` already catches what matters there, which is more work being asked of the renderer.

**One flaw could sink the perf half of the agent.** Once the staleness check makes the owner measure every ten engine commits, the measurement answers the question better than any reviewer. Within a month the agent's perf findings may have nothing left to add. Ship the staleness check now, give the agent's perf section four weeks, and delete it if no finding led to a row in `history.jsonl`.

**Response C:**

The fatal flaw is an agent that carries the detection. The 1.2-second script already detects, deterministically. What it lacks is identity and memory, and both are data problems. The design below fixes the script first and gives the agent only the remaining triage.

**1. Extend `test/repetition_check.py`; do not adopt jscpd.**
- jscpd would be a second detector: a Node dependency with a second definition of "clone". It also silently skips the two files that hold 64 % of the problem.
- Two changes to the script, about 30 lines:
  - Record the SHA-256 of each 8-line window the script already computes in `test/repetition.json`, and fail on any new hash instead of on count growth. That closes the "remove one clone, add another" hole.
  - Add `.qml`, `.glsl`, `.vert` and `.frag` to `sources()`.
- It stays in CI's `fast` lane as the only gate.

**2. Declare deliberate twins as data in the record file.**
- Add a `"twins"` list to `repetition.json`. Each entry holds `{files: [a, b], reason, date}`. No in-code annotations.
- First entry: `VulkanWidget.cpp` and `VulkanHeadlessRenderer.cpp`, with the reason "preview and headless diverge on purpose; no shared base".
- A twin is still counted; it is only exempt from refactor proposals. The entry also adds a drift check: when a commit touches a hashed run in one twin and not in the other, the script prints both locations. That is the bug the owner actually has, and it needs no LLM.

**3. The agent is a weekly advisory job in `nightly.yaml`, never in `ci.yaml`.**
- Trigger: Monday cron plus `workflow_dispatch`.
- Invocation: headless `claude -p --bare --output-format json`, with an API key held in a GitHub environment secret and `permissions: contents: read, issues: write`. `--bare` rules out the subscription token, which is fine.
- `--bare` also keeps `CLAUDE.md` and its board order out of the run. The prompt lives in a new `.github/prompts/clone-audit.md`.
- Input: the script's candidate list plus the twins list. The agent never reads the whole repo.
- Output: one rolling issue, edited in place, of at most five findings. Each finding must name lines to delete. "Extract a base class" is banned in the prompt. A rejected finding becomes a twins entry, and that list is the agent's memory.
- It pushes no branch.
- Cost is about $0.80 a week, with a hard `--max-turns` cap.

**4. "Still optimised" is not an agent job.**
- `test/perf/history.jsonl` and the owner's Mac measure it. CI keeps checking what the scenes ask the renderer to do. Nothing is added here.

In total this adds one JSON key, one prompt file and one cron job.

**Response D:**

The agent must never be the gate. Same commit must give the same verdict, and an LLM cannot promise that. So there are two jobs, and only the deterministic one can go red.

**Fix the ratchet first.** `test/repetition_check.py` compares three integers, so it can be fooled: delete one clone, add another, it passes. The script also has a false-negative bug: `hot` marks windows per file, so two separate clones that sit next to each other merge into one run. Its content hash then matches nothing and it is dropped from the report.

- **Baseline:** record clone identities. `repetition.json` holds the sorted `byContent` hashes the script already computes (`{hash: lines}`).
- **Failure rule:** fail on any hash not in the baseline, even when totals fall.
- **Reproducibility:** the hashes are line-number-free, so editing above a clone changes nothing. Same tree gives the same set.
- **Staleness:** `--update` stays the only way to accept a new clone, and the diff names each clone added or removed.
- **Coverage:** add `qml/**/*.qml` and `assets/shaders/**` to `SOURCES`.
- **Tooling:** skip jscpd. It silently skipped the two biggest files, and a detector that drops input without saying so cannot sit under a gate.

**Declared twins live in one file.** `test/twins.json` lists pairs of `file:function` with the owner's reason. The ratchet still counts them, because growth inside a twin still matters. Only the agent skips them.

**The agent triages candidates; it does not discover.** It runs weekly on `--list` output plus near-miss windows, and its output goes through a validator before anyone reads it.

- **Schema:** reject anything that does not parse.
- **Citations:** every `file:start-end` must exist at the audited SHA.
- **Similarity:** recompute on the cited spans with `difflib.SequenceMatcher` over normalised lines. Below 0.6, drop the finding and log the drop.
- **Twins:** drop any finding that touches a declared twin.
- **Stable ID:** each finding is the hash of the two normalised spans. Issues are keyed on that ID, so the same finding never posts twice, and a closed issue means "rejected, stay silent".

The validator is deterministic, so it runs in the fast lane against recorded agent outputs.

**Test the agent job itself.** Keep a fixture directory with:

- one seeded type-4 duplicate it must report;
- one declared twin it must stay silent on;
- one hallucination trap, a recorded finding citing a line that does not exist, which the validator must reject.

Run this monthly. Recall on the seed is the only honest measure of whether the prompt still works.

**"Still optimised":** CI can only assert the ask-counts that `test/perf/digest.py` already pins. No agent gets an opinion on speed.

**Response E:**

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
