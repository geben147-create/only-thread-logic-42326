"""
LLM-Powered Weight Optimizer for Threads scoring.

Uses Claude Code CLI (Max subscription) to propose new weight configs.
No API key needed — uses the same CLI the user is already running.

Tunable parameters:
  - Phase 1: min_vph_threshold, min_std_floor
  - Phase 2: red_ocean_weight, red_ocean_cap
  - Phase 3: high_threshold, low_threshold
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class WeightConfig:
    """All tunable parameters across Phase 1, 2, and 3."""
    # Phase 1
    min_vph_threshold: float = 50.0
    min_std_floor: float = 5.0
    # Phase 2
    red_ocean_weight: float = 0.5
    red_ocean_cap: float = 1.5
    # Phase 3
    high_threshold: float = 200.0
    low_threshold: float = 75.0
    # Metadata
    iteration: int = 0
    score: float = 0.0
    reasoning: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> WeightConfig:
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in d.items() if k in valid_fields}
        return cls(**filtered)


REPO_ROOT = Path(__file__).parent.parent
WEIGHTS_PATH = REPO_ROOT / "data" / "best_weights.json"
HISTORY_PATH = REPO_ROOT / "data" / "weight_history.json"


def load_best_weights() -> WeightConfig:
    if WEIGHTS_PATH.exists():
        data = json.loads(WEIGHTS_PATH.read_text(encoding="utf-8"))
        return WeightConfig.from_dict(data)
    return WeightConfig()


def save_best_weights(config: WeightConfig) -> None:
    WEIGHTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    WEIGHTS_PATH.write_text(
        json.dumps(config.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def append_history(config: WeightConfig) -> None:
    history: list[dict] = []
    if HISTORY_PATH.exists():
        history = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
    history.append(config.to_dict())
    HISTORY_PATH.write_text(
        json.dumps(history, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


SYSTEM_PROMPT = """\
You are a scoring algorithm optimizer for a Threads post explosion detection system.

The system has 3 tunable phases (platform-agnostic VPH math):
- Phase 1 (z-VPH): min_vph_threshold (10-200), min_std_floor (1-20)
  Controls small-account z-score dampening on Threads. Lower threshold = more dampening.
- Phase 2 (Red Ocean): red_ocean_weight (0.1-2.0), red_ocean_cap (1.1-3.0)
  Controls how much saturated hashtags/topics boost scores. Higher cap = more boost.
- Phase 3 (Output): high_threshold (100-400), low_threshold (30-150)
  final_score = z_vph * multiplier * 50 + 50. Flag is HIGH if final >= high_threshold.
  Raising high_threshold makes it harder to be HIGH.

Your job: given previous weights and their evaluation results, propose
improved weights that maximize the fitness score (higher = better).

Simplicity criterion: when two configs score equally, prefer the one
with fewer corrections_applied and thresholds closer to the defaults.

RESPOND ONLY with valid JSON, no markdown fences:
{
  "min_vph_threshold": <float>,
  "min_std_floor": <float>,
  "red_ocean_weight": <float>,
  "red_ocean_cap": <float>,
  "high_threshold": <float>,
  "low_threshold": <float>,
  "reasoning": "<1-2 sentence explanation>"
}
"""


class WeightGenerator:
    """Calls Claude Code CLI (Max subscription) to propose weights."""

    def __init__(self, model: str = "sonnet"):
        self.model = model
        self._verify_cli()

    @staticmethod
    def _verify_cli() -> None:
        try:
            result = subprocess.run(
                ["claude", "--version"],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode != 0:
                raise RuntimeError(
                    "claude CLI not found. Install: npm install -g @anthropic-ai/claude-code"
                )
        except FileNotFoundError:
            raise RuntimeError(
                "claude CLI not found. Install: npm install -g @anthropic-ai/claude-code"
            )

    def propose(
        self,
        current_weights: WeightConfig,
        eval_summary: str,
    ) -> WeightConfig:
        user_msg = (
            f"Current weights (iteration {current_weights.iteration}):\n"
            f"{json.dumps(current_weights.to_dict(), indent=2)}\n\n"
            f"Evaluation results:\n{eval_summary}\n\n"
            f"Propose improved weights for iteration {current_weights.iteration + 1}."
        )

        full_prompt = f"{SYSTEM_PROMPT}\n\n{user_msg}"

        result = subprocess.run(
            [
                "claude",
                "-p",
                "--model", self.model,
            ],
            input=full_prompt,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            timeout=300,
        )

        raw_text = (result.stdout or "").strip()
        if not raw_text:
            raise RuntimeError("Claude CLI returned empty output")

        if "```" in raw_text:
            start = raw_text.find("{")
            end = raw_text.rfind("}") + 1
            raw_text = raw_text[start:end]

        proposed = json.loads(raw_text)

        return WeightConfig(
            min_vph_threshold=float(proposed["min_vph_threshold"]),
            min_std_floor=float(proposed["min_std_floor"]),
            red_ocean_weight=float(proposed["red_ocean_weight"]),
            red_ocean_cap=float(proposed["red_ocean_cap"]),
            high_threshold=float(proposed.get("high_threshold", 200.0)),
            low_threshold=float(proposed.get("low_threshold", 75.0)),
            iteration=current_weights.iteration + 1,
            reasoning=proposed.get("reasoning", ""),
        )
