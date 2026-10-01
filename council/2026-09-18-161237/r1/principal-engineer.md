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
