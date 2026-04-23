# AUDIT.md — Formula Correctness Audit (v0.2.0 → v0.3.0)

> Autoresearch-style validation of all 26 formulas against realistic
> Threads scenarios. Method: stress-test each formula with data that
> actual users would feed in, identify failure modes, fix.

Performed 2026-04-24. Runs on each public release going forward.

---

## Summary

| Severity | Count | Formulas |
|---|---|---|
| 🔴 P0 correctness bug | 1 | posting_consistency (CH-5) |
| 🟡 P1 usability gap | 1 | account_health_score (CH-7) |
| 🟢 P2 doc clarification | 1 | modified_z (D-3b) |
| ✅ Verified OK | 23 | all others |

All fixed in v0.3.0. Test count: 118 → 132 (14 new tests added).

---

## 🔴 P0 — posting_consistency collapses to zero on real data

### Before (v0.2.0, BUG)

```python
def posting_consistency(post_timestamps_unix):
    intervals = [...]  # seconds
    std = statistics.stdev(intervals)
    return 1.0 / (1.0 + std)   # ← unit-dependent!
```

### Repro

```python
# User posts daily at roughly the same time, ±1 hour jitter
timestamps = [i * 86400 + random.randint(-3600, 3600) for i in range(10)]
posting_consistency(timestamps)
# → 0.000261   ← essentially zero for a clearly regular schedule
```

### Why it broke

`stdev` returns value in **seconds**. A daily schedule with ±1h
jitter has stdev ≈ 3800s, so `1/(1+3800) ≈ 0.0003`. The formula
"works" only when intervals are in the range 0-1 seconds, which no
real Threads account matches.

### Fix (v0.3.0): coefficient of variation

```python
cv = stdev / mean            # dimensionless ratio
return 1.0 / (1.0 + cv)
```

Scale-free: a daily schedule ±1h and a monthly schedule ±1day
both score ~0.96 (same relative variance).

### Verification
- Daily posting, ±1h jitter: `0.000261` → `0.957` ✓
- Monthly posting, ±1day jitter: same score (scale-free) ✓
- Perfectly regular: `1.0` ✓
- Highly irregular: `< 0.6` ✓

---

## 🟡 P1 — account_health_score has no normalization helpers

### Before (v0.2.0)

`account_health_score` takes 7 parameters normalized to 0-100, but
the library provided no way to produce those normalized values.
Users had to invent their own thresholds, often incorrectly.

```python
# What does the user do with raw engagement_rate=0.05?
score = account_health_score(
    engagement_rate_norm=??,  # 5? 50? 100?
    ...
)
```

### Fix (v0.3.0): 7 `normalize_*` helpers

Each helper maps a raw metric to a 0-100 score against a domain-
reasonable target:

| Helper | Target |
|---|---|
| `normalize_engagement_rate` | 5% ER → 100 |
| `normalize_posting_consistency` | scales 0-1 → 0-100 |
| `normalize_views_per_follower` | 10% VPF → 100 |
| `normalize_content_efficiency` | 10K views/post → 100 (tunable) |
| `normalize_posting_frequency` | 30 posts/month → 100 |
| `normalize_follower_conversion` | 2% conv → 100 |
| `normalize_audience_credibility` | "REAL" → 100, "SUSPICIOUS" → 30 |

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
# → 97.5
```

Each target is a reasonable Threads default but tunable per domain.

---

## 🟢 P2 — modified_z docstring ambiguous

### Before (v0.2.0)

`modified_z(x, values)` — docstring did not say whether `values`
should include `x` or not. In practice the difference is tiny
(`3368.8` vs `3368.6` on a 1M outlier), but the convention was
undocumented.

### Fix (v0.3.0)

Docstring updated to:

> `values`: The reference distribution. **May include x or not** —
> results barely differ (see audit §2). Convention: pass the full
> history including the current observation.

---

## ✅ Verified OK (no changes needed)

Stress-tested with realistic Threads inputs; behavior matches spec:

| ID | Formula | Checked |
|---|---|---|
| D-4a | alert_level | thresholds work at normal + dampened z scales |
| D-2a | surge_z | handles len<2, zero-std cases |
| A-1 | z_vph | log1p dampening + std_floor work correctly |
| A-2 | red_ocean_multiplier | cap enforced, invalid cap raises |
| A-3 | final_score_v1 | negative z produces negative final (expected) |
| B-4a | engagement_rate | views=0 safe, matches industry (likes+replies) |
| C-1a | like_ratio | views=0 safe |
| CH-1 | account_momentum | prev=0 guards |
| CH-2 | views_per_follower | followers=0 safe |
| CH-3 | outlier_ratio | avg=0 safe |
| CH-4 | content_efficiency | posts=0 safe |
| CH-6 | audience_credibility | threshold boundary correct |
| C-2b | follower_conversion | views=0 safe |
| D-4b | growth_trigger | simple boolean |
| T-1 | repost_rate | views=0 safe |
| T-2 | quote_rate | views=0 safe |
| T-3 | viral_velocity_24h | 0h→1h floor, >24h→24h cap |
| T-4 | reply_ratio | views=0 safe |
| T-5 | threads_satisfaction | saturation at 100, all-zero gives 0 |
| T-6 | media_type_branch | unknown types fall back to default |
| T-7 | share_rate | views=0 safe |
| T-8 | quote_to_reply_ratio | replies=0 safe |
| T-9 | link_attachment_penalty | None and "" both → 1.0 |

---

## Known limitations (not bugs — document in user-facing docs)

1. **threads_satisfaction targets are aggressive.** reply=5%, repost=3%,
   quote=2%, follower_gain=1% are viral-post levels. Typical organic
   posts score 15-25/100 on this formula. The absolute number is less
   informative than relative comparison across your own posts.
2. **alert_level(z > 5.0) = "viral"** is unreachable for small accounts
   after log1p dampening (max dampened z ≈ log1p(500) ≈ 6.2). This
   matches design intent — "viral" should be a normal-account signal.
3. **audience_credibility threshold 5%** follows NoxInfluencer but
   Threads industry norms are not yet established. Consider tuning
   against your domain.
