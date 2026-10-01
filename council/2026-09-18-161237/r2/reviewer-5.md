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
