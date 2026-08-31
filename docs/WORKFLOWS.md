# What guards the repo

Three places, split by what each can actually decide. Nothing blocks a push.

| where | what it checks | when | blocks? |
|---|---|---|---|
| **GitHub Actions** | types, the suites, docs/test coverage of new API, qmllint, formatting, the build, the C++ unit tests, the QML chrome, `eg.py` still renders, the bake digest | every push and PR | the run goes red, the push already landed |
| **`make check`** | visual regression, C++ unit tests, bake digest, performance — and RECORDS the timings into `test/perf/history.jsonl` | when you ask for it | no |
| **`/ship`** | writes the docs, tests and examples a change owes | before committing | no |
| `.githooks/pre-commit` | what the repo forgot to commit, coverage, types, the QML chrome (~15 s) — armed with `make arm` | on commit, once armed | yes |

## GitHub does the waiting

The `fast` job of `.github/workflows/ci.yaml` runs the suites and pyright. It
also runs `test/coverage_check.py --pushed`, which reads every public symbol the
pushed range adds to the library (`videocode/`, `src/`, `include/`) and asks:

- is there a docstring where it is defined?
- is it mentioned in `docs/*.md`?
- is it mentioned in `test/`?

For C++ it reads headers only: a type declared in a `.cpp` is reachable by
nobody, so it is not surface. Asking a function-local helper for a documentation
page is a false alarm, and a false alarm on a hook is how a team learns to type
`--no-verify`.

It never writes anything, and it greps for names — so it cannot see a docstring
that lies or a test that asserts nothing. It is the floor, not the ceiling. When
it goes red, run `/ship` and push again. A deliberate exception is fine: say why
in the commit message.

The build job now renders `eg.py` too. That file is the living showcase of every
feature worth seeing, so if it stops rendering, an example in the docs has gone
stale — which is the failure mode documentation actually has.

## One rule, one place

Two of the defects this repository was audited for were a rule written twice
whose copies agreed by coincidence. `Context.channelKey` is the answer to *what
name does this piece of state answer to*: `Args:<name>` for an `args` shader,
the class name for everything else. It is asked by `Context.apply`, which
stores a frame under that key, and by `Input.apply`, which decides from it
whether two statements are rivals. Had those two ever drifted apart, the editor
would have warned about the wrong pairs while the stack stored under a
different name, and nothing would have said so. `test/contention_test.py`
asserts that they agree — not that either is right on its own, which is the
part a single-sided test would have missed.

## What GitHub cannot check, and why

**Visual regression.** The goldens in `test/visual/golden/` were rendered on
Apple Silicon through Metal. The CI runner has no GPU and falls back to software
Vulkan (`mesa-vulkan-drivers`), whose antialiasing differs — every scene would
fail, for reasons that have nothing to do with the change. Comparing pixels
means comparing them against the same renderer.

**Performance.** A shared runner's timings, on software rendering, say nothing
about a baseline measured on this machine — measured, the runner renders at
589 ms/frame against ~8 ms here, which is a different rasterizer rather than a
noisier one. So the split is: **this machine measures, GitHub remembers.**
`make check` appends one line per commit to `test/perf/history.jsonl`, which
travels in the commit like a golden, and the `history` job publishes the curve
without ever running a benchmark. What CI *can* compute exactly is what the
scenes ASK the renderer to do — `test/perf/digest.py`, a per-scene hash of the
bake, held to zero tolerance on any runner.

A threshold on wall time would either never
fire or fire constantly.

Both live in `make check` instead:

```bash
make check
```

- **Visual** — renders every scene in `test/visual/scenes/` and compares against
  its golden. Only failures *not* listed in `test/visual/known_failures.txt`
  count, so "already broken" is never mistaken for "broken just now".
- **Performance** — `test/perf/guard.py` re-runs the benchmark and compares
  against `test/perf/baseline.json`: load time (+30 % tolerated), render speed
  (+20 %), total wall time (+20 %), peak memory (+25 %). Timings keep the best
  of three runs; the mean drags in whatever else the laptop was doing.

Never run a blanket `--update-golden` to make a suite green. A golden can be
recording a bug: the `matte` golden did exactly that on 2026-07-28, blessing a
word whose letters were mis-spaced. Look at the image, decide whether the new
render is right, and regenerate that one scene alone.

Re-baselining performance is a decision, not a chore:

```bash
python3 test/perf/guard.py --update
```

Do it when a change makes the renderer legitimately slower (a feature worth its
cost) or legitimately faster (then the new floor protects the win), and say
which in the commit message. `docs/optimization.md` records how the current
numbers were earned — start there before accepting a regression.

## `/ship` — the half a script cannot do

CI decides whether a change is *allowed* in. The skill makes it *worth* letting
in: it reads the diff, writes the missing docstrings, the `docs/*.md` entries and
the tests, adds a **runnable** example for each, and checks whether the
surrounding documentation went stale — a wrong doc is worse than a missing one,
because it is trusted.

Deterministic checks block; judgement writes. Keeping them apart is why nothing
on your critical path is slow.

## The optional local hook

If you would rather catch the coverage debt before pushing than read it off a
red CI run:

```bash
git config core.hooksPath .githooks     # arms .githooks/pre-commit (~12 s)
git config --unset core.hooksPath       # disarms it
```

It runs the coverage check only — types and tests stay on GitHub, and nothing
gated to a push. `git commit --no-verify` bypasses it once.
