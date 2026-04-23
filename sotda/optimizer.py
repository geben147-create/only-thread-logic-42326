"""
Autoresearch Orchestrator — Threads Weight Optimization Loop.

One cycle:
  1. EVALUATE: Score current weights against test battery
  2. GENERATE: LLM proposes improved weights
  3. INJECT:   Re-evaluate with new weights, keep if better
  4. LOG:      Append to results.tsv + logs/

Usage:
  python -m sotda.optimizer                  # Run 1 cycle
  python -m sotda.optimizer --cycles 5       # Run 5 cycles
  python -m sotda.optimizer --cycles 10 --dry-run  # No LLM calls, eval only
"""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sotda.evaluator import evaluate_weights
from sotda.generator import (
    WeightConfig,
    WeightGenerator,
    append_history,
    load_best_weights,
    save_best_weights,
)

# ──────────────────────────────────────────────
# Logging Setup
# ──────────────────────────────────────────────

LOGS_DIR = REPO_ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)
RESULTS_TSV = REPO_ROOT / "results.tsv"

log_file = LOGS_DIR / f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.log"

_stream_handler = logging.StreamHandler(
    open(sys.stdout.fileno(), mode="w", encoding="utf-8", closefd=False)
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-5s | %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        _stream_handler,
        logging.FileHandler(log_file, encoding="utf-8"),
    ],
)
log = logging.getLogger("optimizer")


# ──────────────────────────────────────────────
# results.tsv (karpathy-style)
# ──────────────────────────────────────────────

TSV_HEADER = (
    "cycle\tfitness\tstatus\tmin_vph_thr\tstd_floor\tocean_weight\t"
    "ocean_cap\thigh_thr\tlow_thr\treasoning"
)


def _git_short_sha() -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=REPO_ROOT, stderr=subprocess.DEVNULL,
        )
        return out.decode().strip()
    except Exception:
        return "no-git"


def append_tsv_row(config: WeightConfig, status: str) -> None:
    if not RESULTS_TSV.exists():
        RESULTS_TSV.write_text(TSV_HEADER + "\n", encoding="utf-8")
    reasoning = (config.reasoning or "").replace("\t", " ").replace("\n", " ")
    row = (
        f"{config.iteration}\t{config.score:.2f}\t{status}\t"
        f"{config.min_vph_threshold}\t{config.min_std_floor}\t"
        f"{config.red_ocean_weight}\t{config.red_ocean_cap}\t"
        f"{config.high_threshold}\t{config.low_threshold}\t"
        f"{reasoning}"
    )
    with RESULTS_TSV.open("a", encoding="utf-8") as f:
        f.write(row + "\n")


# ──────────────────────────────────────────────
# Orchestrator
# ──────────────────────────────────────────────

def run_cycle(
    generator: WeightGenerator | None,
    current: WeightConfig,
    cycle_num: int,
) -> WeightConfig:
    """Execute one evaluate → generate → inject cycle."""

    log.info("=" * 60)
    log.info(f"CYCLE {cycle_num} START (git={_git_short_sha()})")
    log.info("=" * 60)

    # Step 1: Evaluate current weights
    log.info("[1/3] EVALUATE current weights")
    score, summary = evaluate_weights(current)
    current.score = score
    log.info(f"Current fitness: {score:.0f}%")
    for line in summary.split("\n"):
        log.info(f"  {line}")

    # Step 2: Generate new weights via LLM
    if generator is None:
        log.info("[2/3] GENERATE skipped (dry-run mode)")
        append_tsv_row(current, status="baseline")
        return current

    log.info("[2/3] GENERATE - asking LLM for improved weights...")
    try:
        proposed = generator.propose(current, summary)
        log.info(f"LLM proposed (iteration {proposed.iteration}):")
        log.info(f"  min_vph_threshold: {current.min_vph_threshold} -> {proposed.min_vph_threshold}")
        log.info(f"  min_std_floor:     {current.min_std_floor} -> {proposed.min_std_floor}")
        log.info(f"  red_ocean_weight:  {current.red_ocean_weight} -> {proposed.red_ocean_weight}")
        log.info(f"  red_ocean_cap:     {current.red_ocean_cap} -> {proposed.red_ocean_cap}")
        log.info(f"  high_threshold:    {current.high_threshold} -> {proposed.high_threshold}")
        log.info(f"  low_threshold:     {current.low_threshold} -> {proposed.low_threshold}")
        log.info(f"  reasoning: {proposed.reasoning}")
    except Exception as e:
        log.error(f"LLM call failed: {e}")
        append_tsv_row(current, status="crash")
        return current

    # Step 3: Inject & re-evaluate
    log.info("[3/3] INJECT - evaluating proposed weights...")
    new_score, new_summary = evaluate_weights(proposed)
    proposed.score = new_score
    log.info(f"Proposed fitness: {new_score:.0f}%")
    for line in new_summary.split("\n"):
        log.info(f"  {line}")

    append_history(proposed)

    if new_score > score:
        log.info(f"IMPROVED: {score:.0f}% -> {new_score:.0f}% - saving new best weights")
        save_best_weights(proposed)
        append_tsv_row(proposed, status="keep")
        return proposed
    elif new_score == score:
        log.info(f"TIE: {score:.0f}% == {new_score:.0f}% - keeping current (simpler)")
        save_best_weights(current)
        append_tsv_row(proposed, status="discard")
        return current
    else:
        log.info(f"NO IMPROVEMENT: {score:.0f}% >= {new_score:.0f}% - keeping current weights")
        save_best_weights(current)
        append_tsv_row(proposed, status="discard")
        return current


def main() -> None:
    parser = argparse.ArgumentParser(description="Autoresearch weight optimization loop")
    parser.add_argument("--cycles", type=int, default=1, help="Number of optimization cycles")
    parser.add_argument("--dry-run", action="store_true", help="Evaluate only, no LLM calls")
    args = parser.parse_args()

    log.info("SOTDA Threads - Autoresearch Optimizer")
    log.info(f"Cycles: {args.cycles} | Dry-run: {args.dry_run}")
    log.info(f"Log file: {log_file}")
    log.info(f"Results TSV: {RESULTS_TSV}")

    current = load_best_weights()
    log.info(f"Loaded weights (iteration {current.iteration}): "
             f"{json.dumps(current.to_dict(), indent=2)}")

    generator = None
    if not args.dry_run:
        try:
            generator = WeightGenerator()
            log.info("Claude CLI (Max subscription) connected")
        except RuntimeError as e:
            log.error(str(e))
            log.info("Falling back to dry-run (eval only)")

    for i in range(1, args.cycles + 1):
        current = run_cycle(generator, current, i)

    log.info("=" * 60)
    log.info("FINAL WEIGHTS:")
    log.info(json.dumps(current.to_dict(), indent=2))
    log.info(f"Final fitness: {current.score:.0f}%")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
