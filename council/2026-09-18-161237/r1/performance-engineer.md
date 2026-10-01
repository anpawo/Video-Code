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
