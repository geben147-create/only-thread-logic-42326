# Formula Correctness Audit - v0.2.0 to v0.3.0

This audit validates all 26 formulas against realistic Threads scenarios. The method is simple: stress-test each formula with data that real users would feed in, identify failure modes, fix the formula or documentation, and add regression tests.

Performed: 2026-04-24

## Summary

| Severity | Count | Formulas |
|---|---:|---|
| P0 correctness bug | 1 | `posting_consistency` (CH-5) |
| P1 usability gap | 1 | `account_health_score` (CH-7) |
| P2 documentation clarification | 1 | `modified_z` (D-3b) |
| Verified OK | 23 | all others |

All findings were fixed in v0.3.0. Test count increased from 118 to 132.

## P0 - posting_consistency collapsed on real data

### Before

```python
def posting_consistency(post_timestamps_unix):
    intervals = [...]
    std = statistics.stdev(intervals)
    return 1.0 / (1.0 + std)
```

The formula used a standard deviation measured in seconds. A regular daily schedule with plus/minus one hour of jitter produced a standard deviation around 3,800 seconds, making the score nearly zero even though the schedule was clearly consistent.

### Reproduction

```python
timestamps = [i * 86400 + random.randint(-3600, 3600) for i in range(10)]
posting_consistency(timestamps)
# old result: about 0.000261
```

### Fix

Use coefficient of variation:

```python
cv = stdev / mean
return 1.0 / (1.0 + cv)
```

This makes the formula scale-free. A daily schedule with one-hour jitter and a monthly schedule with one-day jitter now produce similar high scores because their relative variance is similar.

### Verification

- Daily posting with one-hour jitter: about `0.957`
- Monthly posting with one-day jitter: similar score
- Perfectly regular schedule: `1.0`
- Highly irregular schedule: below `0.6`

## P1 - account_health_score lacked normalization helpers

`account_health_score` accepts seven normalized 0-100 inputs, but v0.2.0 did not provide a standard way to normalize raw metrics. Users had to invent thresholds themselves.

### Fix

v0.3.0 adds helper functions:

| Helper | Target |
|---|---|
| `normalize_engagement_rate` | 5% ER maps to 100 |
| `normalize_posting_consistency` | 0-1 maps to 0-100 |
| `normalize_views_per_follower` | 10% VPF maps to 100 |
| `normalize_content_efficiency` | 10K views/post maps to 100 |
| `normalize_posting_frequency` | 30 posts/month maps to 100 |
| `normalize_follower_conversion` | 2% conversion maps to 100 |
| `normalize_audience_credibility` | `REAL` maps to 100, `SUSPICIOUS` maps to 30 |

### Usage

```python
score = account_health_score(
    engagement_rate_norm=normalize_engagement_rate(0.05),
    posting_consistency_norm=normalize_posting_consistency(0.9),
    views_per_follower_norm=normalize_views_per_follower(0.1),
    content_efficiency_norm=normalize_content_efficiency(15_000),
    posting_frequency_norm=normalize_posting_frequency(30),
    follower_conversion_norm=normalize_follower_conversion(0.02),
    audience_credibility_norm=normalize_audience_credibility("REAL"),
)
```

The defaults are reasonable starting points and can be tuned per domain.

## P2 - modified_z docstring was ambiguous

The old docstring did not state whether `values` should include `x`. The difference is usually tiny, but ports and integrations need a convention.

### Fix

The docstring now states:

> `values` is the reference distribution. It may include `x` or not; results barely differ. Convention: pass the full history including the current observation.

## Verified OK

These formulas were stress-tested and did not require implementation changes:

| ID | Formula | Check |
|---|---|---|
| D-4a | `alert_level` | thresholds work at normal and dampened z scales |
| D-2a | `surge_z` | handles small windows and zero standard deviation |
| A-1 | `z_vph` | log scaling and standard deviation floor work |
| A-2 | `red_ocean_multiplier` | cap enforced, invalid cap raises |
| A-3 | `final_score_v1` | negative z behavior is intentional |
| B-4a | `engagement_rate` | zero views safe, likes plus replies |
| C-1a | `like_ratio` | zero views safe |
| CH-1 | `account_momentum` | previous-period zero guards |
| CH-2 | `views_per_follower` | followers zero guard |
| CH-3 | `outlier_ratio` | baseline zero guard |
| CH-4 | `content_efficiency` | post count zero guard |
| CH-6 | `audience_credibility` | threshold boundary correct |
| C-2b | `follower_conversion` | views zero guard |
| D-4b | `growth_trigger` | boolean trigger works |
| T-1 | `repost_rate` | views zero guard |
| T-2 | `quote_rate` | views zero guard |
| T-3 | `viral_velocity_24h` | 1h floor and 24h cap |
| T-4 | `reply_ratio` | views zero guard |
| T-5 | `threads_satisfaction` | caps at 100, all-zero returns 0 |
| T-6 | `media_type_branch` | unknown media type fallback |
| T-7 | `share_rate` | views zero guard |
| T-8 | `quote_to_reply_ratio` | replies zero guard |
| T-9 | `link_attachment_penalty` | `None` and empty string both return 1.0 |

## Known limitations

1. `threads_satisfaction` targets are intentionally aggressive. Typical organic posts may score 15-25/100.
2. `alert_level(z > 5.0) = "viral"` is hard to reach for small accounts after log scaling. This is intentional.
3. `audience_credibility` uses a 5% threshold borrowed from adjacent creator analytics norms. Tune it against your domain if needed.
