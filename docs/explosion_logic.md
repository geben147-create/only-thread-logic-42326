# Explosion Focus Scoring Logic

SOTDA Threads focuses on **relative explosion**: how strongly a post outperforms the author's own baseline. It does not try to measure global trend size by absolute views alone.

Red ocean topics are treated as demand accelerators. If a post breaks out inside a saturated topic, that is stronger evidence of real demand, not a reason to discard it.

## Phase 1 - Post Explosion Score

Core metric: z-VPH, or views-per-hour z-score.

```text
z_vph = (current_vph - author_avg_vph) / author_std_vph
```

Inputs:

- `current_vph`: current post views divided by hours since posting.
- `author_avg_vph`: average VPH across the author's recent posts.
- `author_std_vph`: standard deviation of VPH across the author's recent posts.

Small-account correction:

- Apply a minimum standard deviation floor to avoid division by near-zero values.
- If the author's average VPH is below the small-account threshold, apply `log1p` dampening.

This prevents tiny accounts from producing absurd z-scores when a post moves from 5 views/hour to 100 views/hour, while still allowing genuine breakouts to score high.

## Phase 2 - Red Ocean Multiplier

Core metric: topic saturation index.

```text
multiplier = 1 + min(topic_saturation_index * weight, cap - 1)
```

Interpretation:

- Low saturation means the topic is niche; multiplier stays near 1.0.
- High saturation means the topic is crowded; a breakout there gets a bonus.
- The cap prevents runaway scores.

Threads does not expose keyword search volume. A practical implementation should derive topic saturation from recent hashtag or topic-tag frequency.

## Phase 3 - Usability Output

The pipeline returns separated fields instead of one opaque score.

```json
{
  "post_burst_score": 8.44,
  "red_ocean_multiplier": 1.4,
  "final_score": 640.8,
  "usability_flag": "HIGH",
  "corrections_applied": []
}
```

Field meanings:

- `post_burst_score`: pure account-relative burst signal.
- `red_ocean_multiplier`: demand-context multiplier.
- `final_score`: normalized score used for thresholding.
- `usability_flag`: `HIGH`, `MEDIUM`, or `LOW`.
- `corrections_applied`: transparency log for small-account corrections.

## Decision Log

| Dimension | Alternative | SOTDA choice | Reason |
|---|---|---|---|
| Core metric | absolute VPH | account-relative z-VPH | breakout should be measured against the author's baseline |
| Red ocean | filter out crowded topics | multiply proven demand | viral signal in a crowded topic is valuable |
| Architecture | one unified score | 3-phase separation | easier to debug, tune, and integrate |
| Platform signals | YouTube retention/watch time | Threads reposts/quotes/shares | Threads API does not expose retention signals |

## Practical Defaults

| Parameter | Default | Purpose |
|---|---:|---|
| `min_vph_threshold` | 50.0 | small-account detection |
| `min_std_floor` | 5.0 | zero-division and noise guard |
| `red_ocean_weight` | 0.5 | saturation bonus strength |
| `red_ocean_cap` | 1.5 | maximum multiplier |
| `high_threshold` | 210.0 | `HIGH` cutoff |
| `low_threshold` | 75.0 | `MEDIUM` cutoff |

These defaults are tuned against the built-in `TEST_BATTERY`. For a production domain, collect labeled examples and tune thresholds locally.
