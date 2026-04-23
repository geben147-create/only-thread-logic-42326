# SPEC.md — Language-Agnostic Formula Specification (Threads)

> Port the SOTDA Threads scoring math to ANY language (Rust, Go, TS,
> Java, C#, Kotlin, Swift, etc.). The Python code in `sotda/` is one
> reference implementation; the math in this file is the contract.
> Verify against `golden_vectors.json` (1e-9 tolerance).

---

## Type primitives
See `sotda_x` SPEC.md §1 for the cross-language type table. Identical here.

## Helper functions
See `sotda_x` SPEC.md §2 (`clamp`, `median`, `mean`, `stdev`, `log1p`).

---

## Formulas — Threads version (26 total)

> Only the 9 Threads-only formulas differ from X. The 17 common
> formulas are IDENTICAL math (just using Threads-native field names:
> `views`, `replies`, `followers`, `reposts`, `quotes`, `shares`).

### 🟢 COMMON 17

Same math as SOTDA-X's 17 common formulas. See [sotda_x SPEC.md](https://github.com/geben147-create/only-twitter-logic-4.24.26/blob/main/SPEC.md) §Formula 1-17.

Field rename table (X → Threads):
- `impression_count` → `views`
- `impressions_per_follower` → `views_per_follower`
- `tweet_impressions` → `post_views`

---

### 🔵 Threads-only 9 (parallel to X T-1..T-9)

**T-1 repost_rate**: `if views <= 0: 0.0 else reposts / views`
**T-2 quote_rate**: same with `quotes`.
**T-3 viral_velocity_24h**:
```
h = min(max(hours_since_post, 1.0), 24.0)
return reposts / h
```
**T-4 reply_ratio**: `replies / views`.
**T-5 threads_satisfaction**:
```
r  = min(reply_ratio  / 0.05 * 100, 100) if reply_ratio  > 0 else 0
p  = min(repost_rate  / 0.03 * 100, 100) if repost_rate  > 0 else 0
q  = min(quote_rate   / 0.02 * 100, 100) if quote_rate   > 0 else 0
f  = min(follower_gain / 0.01 * 100, 100) if follower_gain > 0 else 0
return 0.35*r + 0.30*p + 0.20*q + 0.15*f
```

**T-6 media_type_branch**: lookup `(high_threshold, low_threshold)`:
- `TEXT_POST` → (180.0, 70.0)
- `IMAGE` → (200.0, 75.0)
- `VIDEO` → (220.0, 80.0)
- `CAROUSEL_ALBUM` → (210.0, 78.0)
- default → (210.0, 75.0)

**T-7 share_rate**: `shares / views`.
**T-8 quote_to_reply_ratio**: `if replies > 0: quotes / replies else 0.0`.
**T-9 link_attachment_penalty**: `0.7 if link_attachment_url else 1.0`.

---

### ❌ NOT AVAILABLE on Threads (available on X)

Threads API does NOT expose `bookmark_count`, `video_view_quartiles`,
or `conversation_id`-level reply aggregates. If your use case needs
these signals, use `sotda_x` (X API v2) instead — see
[only-twitter-logic-4.24.26](https://github.com/geben147-create/only-twitter-logic-4.24.26).

---

## Verification

```bash
python -m pytest tests/test_formulas.py
# Or cross-language:
# iterate golden_vectors.json; assert abs(your_impl(vector.input) - vector.expected) < 1e-9
```
