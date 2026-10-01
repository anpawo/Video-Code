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
