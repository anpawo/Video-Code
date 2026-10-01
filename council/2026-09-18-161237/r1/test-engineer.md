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
