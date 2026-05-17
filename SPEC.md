# SPEC.md - Language-Agnostic Formula Specification for Threads

This document is the contract for porting SOTDA Threads scoring math to other languages such as Rust, Go, TypeScript, Java, C#, Kotlin, and Swift.

The Python code in `sotda/` is the reference implementation. A port is considered compliant when it matches [golden_vectors.json](golden_vectors.json) within `1e-9` tolerance.

## Type primitives

| Concept | Python | TypeScript | Notes |
|---|---|---|---|
| Number | `float` or `int` | `number` | Use IEEE-754 double precision where possible |
| String enum | `Literal[...]` | string union | Return exact labels |
| Optional string | `str | None` | `string | null | undefined` | Empty string counts as no link |
| Numeric list | `list[float]` | `number[]` | Preserve input order unless a formula sorts internally |
| Pair | `tuple[float, float]` | `[number, number]` | Used by `media_type_branch` |

## Helper functions

Ports should implement these helpers with equivalent behavior:

- `clamp(value, lo, hi)`: bound a number to an inclusive range.
- `median(values)`: median of sorted values; return `0` for empty input only where the Python reference does.
- `mean(values)`: arithmetic mean.
- `stdev(values)`: sample standard deviation.
- `log1p(value)`: natural log of `1 + value`.

## Formulas - Threads version

The library exposes 26 formulas:

- 17 common formulas shared with other SOTDA platforms.
- 9 Threads-only formulas using Threads-native fields.

### Common 17

The common formulas use Threads field names:

| Other platform field | Threads field |
|---|---|
| `impression_count` | `views` |
| `comments` | `replies` |
| `subscribers` | `followers` |
| `channel` | `author` or `account` |
| `video_impressions` | `post_views` |

Common formula names:

```text
modified_z
alert_level
surge_z
z_vph
red_ocean_multiplier
final_score_v1
engagement_rate
like_ratio
account_momentum
views_per_follower
outlier_ratio
content_efficiency
posting_consistency
audience_credibility
follower_conversion
account_health_score
growth_trigger
```

### Threads-only 9

**T-1 repost_rate**

```text
if views <= 0: return 0.0
return reposts / views
```

**T-2 quote_rate**

```text
if views <= 0: return 0.0
return quotes / views
```

**T-3 viral_velocity_24h**

```text
h = min(max(hours_since_post, 1.0), 24.0)
return reposts / h
```

**T-4 reply_ratio**

```text
if views <= 0: return 0.0
return replies / views
```

**T-5 threads_satisfaction**

```text
r = min(reply_ratio / 0.05 * 100, 100) if reply_ratio > 0 else 0
p = min(repost_rate / 0.03 * 100, 100) if repost_rate > 0 else 0
q = min(quote_rate / 0.02 * 100, 100) if quote_rate > 0 else 0
f = min(follower_gain_rate / 0.01 * 100, 100) if follower_gain_rate > 0 else 0
return 0.35 * r + 0.30 * p + 0.20 * q + 0.15 * f
```

**T-6 media_type_branch**

Return `(high_threshold, low_threshold)`.

| `media_type` | Return |
|---|---|
| `TEXT_POST` | `(180.0, 70.0)` |
| `IMAGE` | `(200.0, 75.0)` |
| `VIDEO` | `(220.0, 80.0)` |
| `CAROUSEL_ALBUM` | `(210.0, 78.0)` |
| default | `(210.0, 75.0)` |

**T-7 share_rate**

```text
if views <= 0: return 0.0
return shares / views
```

**T-8 quote_to_reply_ratio**

```text
if replies <= 0: return 0.0
return quotes / replies
```

**T-9 link_attachment_penalty**

```text
return 0.7 if link_attachment_url else 1.0
```

## Not available on Threads

Threads Graph API does not expose these YouTube/X-style signals:

- `bookmark_count`
- `video_view_quartiles`
- watch time or retention
- Shorts duration branching
- conversation-level reply aggregates
- keyword search volume
- revenue or RPM

If your use case requires those fields, use a platform-specific SOTDA package instead.

## Verification

Python:

```bash
python -m pytest tests/test_formulas.py
```

TypeScript:

```bash
node --experimental-strip-types typescript/test/verify_golden.mjs
```

Other languages:

1. Iterate over every vector in `golden_vectors.json`.
2. Call the matching formula with `vector.input`.
3. Assert that the actual result equals `vector.expected`.
4. For numbers, use the file's `tolerance` value.
