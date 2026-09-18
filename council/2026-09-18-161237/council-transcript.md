# Council: 18 September 2026

## Original question

add some ci that use agents to verify that the code doestn have duplicates and is still optimised. no double function, no repeated code, etc... lookup the internet to see what exists and make smth for the project. council meeting

## Framed question

DECISION. Design the CI job that uses AI AGENTS to keep the Video-Code repository free of duplicated code and of code that has stopped being efficient ("no double function, no repeated code, still optimised"). Settle: (1) gate or advisory; (2) when it runs and where its output lands; (3) how it authenticates and what it costs; (4) what the agent may do (read, comment, push a branch); (5) how deliberate twins are declared so it stops proposing abstractions the owner has rejected; (6) whether to extend the existing deterministic ratchet or adopt jscpd; (7) what "still optimised" can honestly mean on a shared runner; (8) how the agent is prompted given the repo's CLAUDE.md. Give ONE concrete design, not a menu.

THE PROJECT. Video-Code: a video editor where the scene is Python, rendered by a C++20/Vulkan engine, with a Qt/QML editor. ~78k lines: Python library (videocode/), C++ (src/, include/), QML (qml/), GLSL (assets/shaders/). Public GitHub repo, solo maintainer, ~12 pushes a day straight to main, main unprotected, three accounts hold push rights (two are being removed). CI is GitHub Actions: pyright, 75 test files, qmllint, clang-format, builds on Linux and macOS, a zero-tolerance "bake digest". House rule, written in docs/WORKFLOWS.md: "Nothing blocks a push" — a red run is information, deterministic checks decide, judgement writes. The owner dislikes unrequested abstraction: his standing instruction to agents is minimal diffs, no speculative helpers, deletion over addition.

FACTS (measured today).
- A deterministic duplication gate ALREADY exists: test/repetition_check.py, in CI's fast lane, 1.2 s. It counts verbatim 8-line runs (whitespace and comments ignored) in .py/.cpp/.hpp and public names nothing mentions, records them in test/repetition.json (975 repeated lines, 68 repetitions, 21 dead names) and fails only on GROWTH. It compares COUNTS, not clone identities: remove one clone, add another, it passes. It does not read QML or GLSL.
- jscpd 4 (token-based) with its defaults reports 0.57 % — and silently skips every file over 1000 lines, which here are the two biggest. With --max-lines raised: 3.57 %, 87 clones, 1329 lines; C++ 8.26 %, Python 0.46 %, GLSL 6.5 %, QML 0.45 %.
- 64 % of all duplication (47 clones, 845 lines) sits between src/window/VulkanWidget.cpp (3.5k lines, preview) and src/vulkan/VulkanHeadlessRenderer.cpp (headless): near-copies by history. A bug fixed in one has to be remembered into the other by hand; one such twin was de-duplicated by hand today.
- No maintained open-source tool detects semantic (type-4) clones; an LLM agent is the practical detector. Published triage results: a tool-first hybrid (deterministic candidates, then an agent loop) removes 94–98 % of static-analysis false positives; one-shot LLM review does far worse; aggressive filtering also suppresses true positives.
- Agent options: anthropics/claude-code-action@v1 (any trigger, `prompt` + `claude_args`, structured JSON output, inline PR comments; pushes a branch, never opens a PR itself) or headless `claude -p --output-format json` (reports total_cost_usd). Anthropic's own managed reviewer always finishes NEUTRAL, never blocks. Auth: an API key (metered) or a one-year subscription token (`claude setup-token`) that shares the owner's interactive 5-hour and weekly limits and whose CI billing is "being reworked". Documented risks: prompt injection from PR content, full output leaking into the public logs of a public repo, secrets withheld from fork PRs.
- Estimated cost (Sonnet-class): ~$0.30 per run triaging candidates on a diff, ~$0.80 for a weekly candidates-first audit, $3–5 if the agent reads the whole repo. At 12 pushes a day, an agent on every push is ~$100 a month; weekly is $4–20.
- Performance cannot be measured on a shared runner (no GPU, ~30x slower): timings are taken on the owner's Mac and travel in test/perf/history.jsonl; CI only checks what the scenes ASK the renderer to do.
- The repo's CLAUDE.md orders any agent to update and publish a status board; a CI agent that loads it inherits that order. `--bare` skips CLAUDE.md but does not accept the subscription token.

STAKES. A noisy or costly reviewer gets muted within a week and the money is wasted; a gate that fails on an LLM's mood breaks the one rule the CI is built on; an agent with write access on an unprotected public main is a supply-chain hole; and an agent that answers every twin with "extract a shared base class" pushes exactly the over-engineering the owner fights. Too timid, and it adds nothing to the 1.2-second script that already exists.


## Workspace context used

Seats are role seats (design-council casting) run under the llm-council protocol, as ~/.claude/CLAUDE.md asks for a technical decision: template slots map Security engineer→security-engineer, Principal engineer→principal-engineer, Performance engineer→performance-engineer, Platform engineer→platform-engineer, Test engineer→test-engineer. A research pass ran first (agent-in-CI options, detectors, cost, what the tools find in this repo); its figures are in the framed question. The HTML report was NOT opened in a browser: the owner's rule is that an agent never opens a window.

---

## Round 1: Advisor responses (raw, de-anonymized)

### Security engineer

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

### Principal engineer

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

### Performance engineer

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

### Platform engineer

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

### Test engineer

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

---

## Anonymization map

Session timestamp: `2026-09-18-161237` · permutation index: `37`

| Advisor | Letter shown to reviewers |
|---|---|
| Security engineer | E |
| Principal engineer Thinker | C |
| Performance engineer | B |
| Platform engineer | A |
| Test engineer | D |

---

## Round 2: Peer reviews (reviewers saw only the anonymized A to E responses)

### Reviewer 1

1. **Strongest: C.**
- It is the only answer that settles all eight points with a small diff.
- Its twin-drift check targets the bug the owner actually has (a fix made in one twin and forgotten in the other), and it needs no LLM.
- Rejected findings become twins entries, so the agent does not propose them again.
- D is the runner-up. The false-negative D found in `test/repetition_check.py` is real, but reading the code it is triggered by overlapping clones, not adjacent ones. D's `difflib` similarity floor of 0.6 would also drop the semantic clones the agent exists to find, including D's own seeded fixture.
- B's two repo claims hold: the last perf row is `96587a7` from 2026-09-06, and 25 engine commits have landed since.

2. **Biggest blind spot: A.**
- It has no declared twins and no memory of rejected findings, although point 5 asked for that explicitly.
- The two Vulkan files hold 64 % of the duplication. They would fill the five-item issue every week, producing exactly the noisy reviewer that gets muted within a week.
- A's prompt carries no ban on proposing abstractions.
- A says `nightly.yaml` has no `workflow_dispatch`; it does, on line 6. Only the comment in that file argues for dropping it.

3. **All five missed where the owner looks.**
- A, C and E edit a rolling issue in place. GitHub does not notify on a body edit, so a new finding reaches nobody.
- B names no destination for its output. D opens one issue per finding and links it to nothing the owner reads.
- The page he keeps open is the board, which `CLAUDE.md` says must agree with `docs/FEATURES_TODO.md`.
- All five treat `CLAUDE.md` and its board order as a threat to strip with `--bare`.
- None routes a finding onto the board, so findings pile up in a third place that contradicts both. Every design is also silent on who adds the board row for each finding.

### Reviewer 2

**1. Strongest: C.**
- It is the only response that settles all eight points with one small design.
- It fixes the ratchet to track clone identities instead of counts.
- It declares twins as data.
- Its drift check between twins catches the bug the owner actually has, with no LLM.
- Caveat: fixing a bug in both twins creates new hashes, so the gate goes red exactly when he does the right thing.
- Caveat: it keeps `workflow_dispatch` next to a secret, and only A restricts the secret to `main`.
- D found a real bug in `test/repetition_check.py`, which I checked: two adjacent clones merge into one run whose hash matches nothing, so both are dropped. D skips auth, cost and triggers.
- B's claim holds: last perf row is `96587a7` on 2026-09-06, with 25 engine commits since.

**2. Biggest blind spot: A.**
- It has no way to declare twins.
- It feeds jscpd's 87 clones to the agent, and 47 of them are the `VulkanWidget.cpp` / `VulkanHeadlessRenderer.cpp` pair the owner has already refused to merge.
- So every weekly top-five will be that same rejected proposal, and the job gets muted within a week.
- It also never says what the prompt contains.

**3. What all five missed.**
- The agent only ever sees what the verbatim detector found.
- Semantic duplicates, the one thing the brief says needs an LLM, never enter any pipeline. D asks for them, then drops them with its 0.6 text-similarity filter, which would also reject its own seeded fixture.
- Growth is already gated, so from week two the agent re-reads the same candidates the script's `--list` already prints, at the same cost.
- Editing an issue body sends no GitHub notification, so nobody learns a new finding was posted.

### Reviewer 3

**1. Strongest: C.**
- It is the only response that settles all eight points in one small design, roughly 30 lines plus a cron job.
- Its drift check between declared twins targets the bug the owner actually has, and it needs no LLM.
- One flaw: it puts the secret-bearing job behind `workflow_dispatch` in `nightly.yaml`. The comment at `nightly.yaml:38-48` says to drop dispatch the day an agent lands there.
- D is the runner-up. Its merged-run bug is real (`repetition_check.py:92-105`): two adjacent clones merge into one run whose hash matches nothing, so both are dropped from the report. But D skips auth, triggers and cost.
- B's claim also checks out: the last perf row is `96587a7` (2026-09-06), with 25 engine commits since.

**2. Biggest blind spot: A.**
- It has no twin declaration and no memory of rejected findings.
- The 64 % twin pair (`VulkanWidget.cpp` and `VulkanHeadlessRenderer.cpp`) will head the issue every Monday with the same "unify them" advice. That is the mute-within-a-week outcome the brief names.
- It also leaves the ratchet's swap-one-clone hole open while adding jscpd as a second definition of "clone".

**3. What all five missed: the agent's input never changes.**
- Every design feeds the agent candidates from a verbatim or token detector, and the gate forbids those candidates from growing.
- From week two the agent re-reads the same ~68 repetitions and produces the same findings.
- Semantic clones, the one thing only an LLM can find, never become candidates. D's "near-miss windows" is the only gesture toward it, and it reaches reworded copies at most.
- Separately, the designs with a rolling issue (A, C, E) rely on `gh issue edit`, which sends no notification, and none of the five feeds `docs/board.html`, the one page the owner watches.

### Reviewer 4

**1. Strongest: D.**
- D is the only response that found a real bug in the existing script, and I confirmed it against the repo. `repetitions()` merges overlapping hot windows into one run per file, so the merged run's hash matches nothing and it is dropped.
- My check found 16 of 155 runs dropped this way, 359 lines in all. The recorded 975 repeated lines is therefore an undercount.
- D also fixes the two ways the agent job would actually get muted: a deterministic validator on the agent's output, and stable finding IDs so that a closed issue means "rejected, stay silent".

**2. Biggest blind spot: A.**
- A leaves `repetition_check.py` "exactly as it is", so the swap hole stays open: remove one clone, add another, and it still passes.
- A declares no deliberate twins, which the framed question asked for as item 5. Its five weekly findings will be the VulkanWidget/VulkanHeadlessRenderer clones every week.
- A's factual claim about `nightly.yaml` is false. The file has `workflow_dispatch:` on line 6, and the comment A cites is about a self-hosted Mac runner, not about secrets.

**3. What all five missed: the findings never reach the owner.**
- Every response treats CLAUDE.md's board order only as a hazard to suppress with `--bare`. None of them puts findings on `docs/board.html` or in `FEATURES_TODO.md`, which is the one page he keeps open and the repo's written record.
- A, C and E edit one rolling issue in place. GitHub sends no notification for a body edit, and A counts that silence as a feature.
- None of the five says who moves an accepted finding to "To do" or a rejected one to "Won't do" with its reason.

### Reviewer 5

1. **Strongest: C.**
- C is the only response that settles all eight points with one design, and it adds the fewest pieces: one JSON key, one prompt file, one cron job.
- Its twin drift check targets the bug the owner actually has, where a fix lands in one renderer and not the other. It needs no LLM.
- C has two flaws. It keeps `workflow_dispatch` next to a secret, which `nightly.yaml:38-48` already documents as an escalation path (A caught this). It also rejects jscpd because it "silently skips" the two biggest files, which only happens with jscpd's defaults.
- D's merge bug is real and should be folded into C. At `repetition_check.py:91-107`, a run made of adjacent clones hashes to nothing and drops out of the report.
- B's figures check out: the last history row is `96587a7` from 2026-09-06, and 25 engine commits since then have no measurement.

2. **Biggest blind spot: A.**
- A has no declaration of deliberate twins and no memory of rejected findings.
- 64 % of the candidates are the VulkanWidget/VulkanHeadlessRenderer pair, so A's five weekly findings will be that same rejected refactor every Monday.
- The owner would mute the job within a week, which is the first stake named in the question.

3. **What all five missed: the agent never sees a semantic clone.**
- Every design feeds the agent only the verbatim or token-level candidates the deterministic detectors already find.
- Two functions that do the same job with different code never become candidates, so they never reach the agent.
- The weekly issue would re-rank what `--list` already prints, which is the "adds nothing to the script" outcome the stakes warn about.
- D's seeded type-4 fixture would fail against D's own pipeline.
- Nobody proposed a cheap semantic candidate source, such as an index of function signatures and docstrings.

---

## Chairman synthesis

### Where the council agrees

- **The agent never gates** (all five). Same commit, same verdict is something an LLM cannot promise; "nothing blocks a push" stays true. Only the deterministic script can turn a run red.
- **Weekly, never on a push or a PR** (platform, security, principal, test). On a public repo this removes the injection surface in one move — no PR text in the prompt, no secret near a fork — and costs about $4 a month instead of about $100.
- **Read-only agent, metered key** (platform, security, principal): `Read,Grep,Glob` only, no shell, no network tool, no GitHub token; a capped API key in one step, `--bare` so the repo's CLAUDE.md is not loaded as orders; a second, LLM-free step does the posting. It pushes nothing.
- **Fix the ratchet before adding anything** (principal, test): record clone IDENTITIES, not three integers — today one clone can be swapped for another unnoticed — and read QML and GLSL. Both reject jscpd as a second definition of "clone".
- **Deliberate twins are data** (principal, test): a file listing the pairs with the owner's reason. Still counted, exempt from refactor proposals; a rejected finding becomes an entry, which is the agent's memory.
- **No agent has an opinion on speed** (performance, test, principal). What CI can say honestly is whether a number EXISTS: the last perf row measures 96587a7 (6 Sept.), 25 engine commits ago.

### Where the council clashes

- **`workflow_dispatch` or not.** Platform drops it (a dispatched run executes the dispatched ref's workflow file, main is unprotected); security and principal keep it. Reviewers checked: `nightly.yaml` does have dispatch, and the comment platform cited is about a self-hosted runner. Settled by platform's OTHER idea: the key lives in a GitHub Environment restricted to `main`, so a dispatch from any other ref gets no secret. Dispatch stays — a job that cannot be run by hand cannot be debugged.
- **One rolling issue or one issue per finding.** Platform, principal, security: one issue edited in place, quiet. Test: one per finding, keyed on a stable ID, closed = rejected. Reviewers broke the tie: editing an issue body notifies nobody. One issue per finding, at most three new ones a run.
- **A perf section in the agent, or none.** Performance: four structural patterns on the engine diff, phrased as questions ending in the command that answers them, on a four-week trial. Test and principal: nothing. Kept as performance framed it — it is the only part of "still optimised" an agent can honestly hold, and its own author gave it an expiry date.

### Blind spots the council caught

- **The agent would never see a semantic clone** (4 of 5 reviewers). Every design fed it only what the verbatim detector already finds, and the gate forbids those from growing: from week two it re-reads the same ~68 repetitions that `--list` prints for free. The one thing only an LLM can find never becomes a candidate — and the test seat's 0.6 text-similarity filter would have thrown out its own seeded fixture. Fix: a deterministic INDEX of every function (name, signature, first docstring line, file:line), with the ones added or changed since the last run marked; the agent looks there for two functions doing one job, then reads the bodies.
- **The findings never reach the owner** (3 of 5). Everyone treated CLAUDE.md's board order as a hazard to strip; nobody routed a finding to the one page he keeps open. CI cannot publish the board, so the bridge is the label: open `audit` issues are To-do rows the next local session adds, closed ones are Won't-do with the closing comment as the reason.
- **The identity ratchet goes red exactly when he does the right thing** (1 reviewer): fixing a bug in BOTH twins creates new hashes. Inside a declared twin pair the rule is therefore growth, not identity — and a clone that VANISHES from a pair is printed, because that is what a fix applied to one side only looks like. The drift check, for free.
- **The existing script undercounts** (test seat, confirmed by 4 reviewers; one measured 16 of 155 runs, 359 lines): overlapping hot windows merge into one run whose hash matches nothing, and it is dropped.

### The recommendation

Build the principal engineer's design — 4 of 5 reviewers picked it — with the test engineer's validator and stable IDs, the security engineer's two-step job, the platform engineer's environment-restricted key and provider-side cap, and the performance engineer's staleness check. Then add what only the review round saw: the function index that gives the agent something a script cannot find, and the `audit` label as the bridge to the board. The chairman overrules the majority on one point: one issue per finding, not a rolling one.

### The one thing to do first

Fix `test/repetition_check.py` — identities instead of counts, the merged-run bug, QML and GLSL — because every other piece reads its output, and today it is undercounting.
