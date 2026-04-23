# program.md — SOTDA Threads Autoresearch Agent

> This file tells the LLM agent how to iterate on weight tuning for the
> Threads explosion-scoring pipeline. Inspired by
> [karpathy/autoresearch](https://github.com/karpathy/autoresearch)'s
> `program.md` convention: a human-maintained instruction file that
> drives an autonomous optimization loop.

## Setup

1. **Agree on a run tag** with the human (e.g. `apr23`). The branch
   `autoresearch/<tag>` must not already exist.
2. **Create the branch**: `git checkout -b autoresearch/<tag>` from `main`.
3. **Read in-scope files**:
   - `README.md` — repository context.
   - `sotda/pipeline.py` — 3-phase algorithm. Do NOT modify.
   - `sotda/evaluator.py` — Threads test battery. Do NOT modify.
   - `sotda/generator.py` — WeightConfig and LLM prompt. Tunable only via `SYSTEM_PROMPT`.
   - `data/best_weights.json` — current best weights (if present).
4. **Verify the baseline**: `python -m sotda.optimizer --dry-run --cycles 1` must succeed and report a fitness percentage.
5. **Initialize results.tsv**: the optimizer auto-creates this on first cycle.
6. **Confirm and go**.

## Experimentation

Each cycle is fast (~seconds, not minutes): evaluate → LLM propose → re-evaluate.

**What you CAN tune:**
- `WeightConfig` fields: `min_vph_threshold`, `min_std_floor`, `red_ocean_weight`, `red_ocean_cap`, `high_threshold`, `low_threshold`.
- The `SYSTEM_PROMPT` in `sotda/generator.py` (LLM reasoning guidance).

**What you CANNOT modify:**
- `sotda/pipeline.py` — the scoring algorithm is the ground truth.
- `sotda/evaluator.py` — `TEST_BATTERY` is the fixed benchmark. Changing it invalidates past results.
- Any formula in `tests/test_formula_triage.py` — these are contracts.

**The goal is simple: maximize fitness on TEST_BATTERY.** Fitness is
the percentage of the 6 known-outcome Threads scenarios that the
pipeline flags correctly.

**Simplicity criterion**: when two configs tie on fitness, prefer the
one with thresholds closer to defaults (`min_vph=50`, `std_floor=5`,
`weight=0.5`, `cap=1.5`, `high=200`, `low=75`) and fewer
`corrections_applied` on average. Hacky thresholds that barely win are
discouraged.

## Output format

After each cycle the optimizer prints:

```
Current fitness: 83%
  Fitness: 83% (5/6 correct)
    [PASS] Normal account genuine Threads explosion: ...
    [FAIL] Moderate Threads explosion in blue ocean stays MEDIUM: ...
LLM proposed (iteration N+1): ...
Proposed fitness: 100%
IMPROVED: 83% -> 100% - saving new best weights
```

## Logging results

The optimizer auto-appends to `results.tsv` (tab-separated):

```
cycle	fitness	status	min_vph_thr	std_floor	ocean_weight	ocean_cap	high_thr	low_thr	reasoning
0	83.33	baseline	50.0	5.0	0.5	1.5	200.0	75.0
1	100.00	keep	50.0	5.0	0.5	1.5	210.0	75.0	raised high_threshold...
2	100.00	discard	50.0	5.0	0.4	1.5	210.0	75.0	lowering ocean_weight...
3	0.00	crash	...	LLM returned invalid JSON
```

Statuses:
- `baseline` — first cycle, no LLM call (`--dry-run`).
- `keep` — proposed fitness > current fitness; new weights saved.
- `discard` — proposed fitness <= current; weights rolled back.
- `crash` — LLM subprocess failed or JSON parse error; current kept.

## The experiment loop

```
LOOP until human interrupts:
  1. Evaluate current weights against TEST_BATTERY
  2. Ask LLM to propose new weights (via `claude -p`)
  3. Re-evaluate proposed weights
  4. Keep if strictly better, discard if worse or tied
  5. Append TSV row, write best_weights.json
```

**Convergence**: once fitness hits 100%, remaining cycles should
discard all proposals (simplicity criterion). The LLM should be told to
stop via the human, or should emit "no further improvement" reasoning.

**NEVER STOP**: once kicked off, keep iterating until the human halts
the loop. If fitness is stuck at a local max, try:
- perturbing thresholds by ±10% and re-evaluating
- widening `red_ocean_weight` exploration range
- re-reading `docs/FORMULA_MASTER.md` for overlooked angles
