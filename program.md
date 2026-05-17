# program.md - SOTDA Threads Autoresearch Agent

This file tells an LLM agent how to iterate on weight tuning for the Threads explosion-scoring pipeline.

It follows the `program.md` convention popularized by `karpathy/autoresearch`: a human-maintained instruction file that drives an autonomous optimization loop.

## Setup

1. Agree on a run tag with the human, for example `apr23`.
2. Create a fresh branch: `git checkout -b autoresearch/<tag>` from `main`.
3. Read the in-scope files:
   - `README.md` - repository context.
   - `sotda/pipeline.py` - 3-phase algorithm. Do not modify.
   - `sotda/evaluator.py` - Threads test battery. Do not modify.
   - `sotda/generator.py` - WeightConfig and LLM prompt. Only `SYSTEM_PROMPT` is tunable.
   - `data/best_weights.json` - current best weights, if present.
4. Verify the baseline: `python -m sotda.optimizer --dry-run --cycles 1`.
5. Let the optimizer create `results.tsv` on the first cycle.
6. Confirm setup, then start the loop.

## Experimentation

Each cycle is fast: evaluate -> LLM propose -> re-evaluate.

Allowed tuning targets:

- `WeightConfig.min_vph_threshold`
- `WeightConfig.min_std_floor`
- `WeightConfig.red_ocean_weight`
- `WeightConfig.red_ocean_cap`
- `WeightConfig.high_threshold`
- `WeightConfig.low_threshold`
- `SYSTEM_PROMPT` in `sotda/generator.py`

Do not modify:

- `sotda/pipeline.py`: the scoring algorithm is the ground truth.
- `sotda/evaluator.py`: `TEST_BATTERY` is the fixed benchmark.
- `tests/test_formula_triage.py`: formula definitions are contracts.

The goal is to maximize fitness on `TEST_BATTERY`. Fitness is the percentage of known-outcome Threads scenarios that the pipeline flags correctly.

When two configurations tie, prefer the one closer to defaults:

- `min_vph_threshold=50`
- `min_std_floor=5`
- `red_ocean_weight=0.5`
- `red_ocean_cap=1.5`
- `high_threshold=210`
- `low_threshold=75`

Also prefer fewer `corrections_applied` on average. Threshold hacks that barely win are discouraged.

## Output format

The optimizer prints a summary like:

```text
Current fitness: 83%
  Fitness: 83% (5/6 correct)
    [PASS] Normal account genuine Threads explosion: ...
    [FAIL] Moderate Threads explosion in blue ocean stays MEDIUM: ...
LLM proposed (iteration N+1): ...
Proposed fitness: 100%
IMPROVED: 83% -> 100% - saving new best weights
```

## Results log

The optimizer appends tab-separated rows to `results.tsv`:

```text
cycle	fitness	status	min_vph_thr	std_floor	ocean_weight	ocean_cap	high_thr	low_thr	reasoning
0	83.33	baseline	50.0	5.0	0.5	1.5	200.0	75.0
1	100.00	keep	50.0	5.0	0.5	1.5	210.0	75.0	raised high_threshold...
2	100.00	discard	50.0	5.0	0.4	1.5	210.0	75.0	lowering ocean_weight...
3	0.00	crash	...	LLM returned invalid JSON
```

Statuses:

- `baseline`: first cycle, no LLM call.
- `keep`: proposed fitness is better than current fitness; new weights saved.
- `discard`: proposed fitness is equal or worse; current weights kept.
- `crash`: LLM subprocess failed or returned invalid JSON; current weights kept.

## Loop

```text
LOOP until human interrupts:
  1. Evaluate current weights against TEST_BATTERY.
  2. Ask the LLM to propose new weights.
  3. Re-evaluate proposed weights.
  4. Keep if strictly better.
  5. Discard if worse or tied.
  6. Append a TSV row and write best_weights.json.
```

Once fitness reaches 100%, remaining cycles should usually discard proposals. If the run is stuck, try:

- perturbing thresholds by +/-10% and re-evaluating
- widening the `red_ocean_weight` exploration range
- re-reading `docs/FORMULA_MASTER.md` for overlooked constraints
