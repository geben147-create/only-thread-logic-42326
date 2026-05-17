# SOTDA Threads Formula Master

This document lists the 26 formulas implemented by `sotda.formulas`.

Threads version:

- 17 common formulas adapted to Threads field names.
- 9 Threads-only formulas using reposts, quotes, shares, media type, and link attachment signals.

## Threads field mapping

| Common concept | Threads field | Notes |
|---|---|---|
| views | `views` from Media Insights | same concept |
| likes | `likes` | same concept |
| comments | `replies` | rename |
| subscribers | `followers` | rename |
| channel | account / owner / author | rename |
| shares | `shares` | Threads-native |
| reposts | `reposts` | Threads-native |
| quotes | `quotes` | Threads-native |
| media type | `media_type` | `TEXT_POST`, `IMAGE`, `VIDEO`, `CAROUSEL_ALBUM` |
| external link | `link_attachment_url` | used for link penalty |
| watch time | not available | cannot compute retention |
| keyword volume | not available | derive saturation from observed topics |
| revenue/RPM | not available | out of scope for Threads |

## Common formulas - 17

### Trend detection

| ID | Formula | Output | Definition |
|---|---|---|---|
| D-3b | `modified_z` | numeric z-score | `0.6745 * (x - median) / MAD` |
| D-4a | `alert_level` | label | `viral`, `surge`, `trending`, `watch`, or `none` |
| D-2a | `surge_z` | numeric z-score | `(today - rolling_mean) / rolling_std` |

### Post analysis

| ID | Formula | Output | Definition |
|---|---|---|---|
| A-1 | `z_vph` | `(score, corrections)` | account-relative VPH z-score with small-account correction |
| A-2 | `red_ocean_multiplier` | multiplier | `1 + min(saturation * weight, cap - 1)` |
| A-3 | `final_score_v1` | numeric score | `z * multiplier * scale + base` |
| B-4a | `engagement_rate` | ratio | `(likes + replies) / views` |
| C-1a | `like_ratio` | ratio | `likes / views` |

### Account analysis

| ID | Formula | Output | Definition |
|---|---|---|---|
| CH-1 | `account_momentum` | multiplier | `(views_30d / views_prev_30d) * (followers_30d / followers_prev_30d)` |
| CH-2 | `views_per_follower` | ratio | `avg_views_90d / total_followers` |
| CH-3 | `outlier_ratio` | multiplier | `post_views / account_avg_views` |
| CH-4 | `content_efficiency` | views/post | `views_30d / posts_30d` |
| CH-5 | `posting_consistency` | 0-1 score | `1 / (1 + stdev(intervals) / mean(intervals))` |
| CH-6 | `audience_credibility` | label | `REAL` if follower engagement is at least 5%, else `SUSPICIOUS` |
| C-2b | `follower_conversion` | ratio | `followers_gained / views` |
| CH-7 | `account_health_score` | 0-100 score | weighted composite of seven normalized account metrics |
| D-4b | `growth_trigger` | boolean | `growth_7d_ratio > 2.0` |

### Account health weights

| Weight | Input | Meaning |
|---:|---|---|
| 25% | normalized engagement rate | reaction strength |
| 15% | normalized posting consistency | schedule reliability |
| 15% | normalized views per follower | follower quality |
| 15% | normalized content efficiency | views per post |
| 10% | normalized posting frequency | posting cadence |
| 10% | normalized follower conversion | conversion from views to followers |
| 10% | normalized audience credibility | authenticity signal |

Normalization helpers are included in `sotda.formulas`.

## Threads-only formulas - 9

| ID | Formula | Output | Definition |
|---|---|---|---|
| T-1 | `repost_rate` | ratio | `reposts / views` |
| T-2 | `quote_rate` | ratio | `quotes / views` |
| T-3 | `viral_velocity_24h` | reposts/hour | `reposts / clamp(hours_since_post, 1, 24)` |
| T-4 | `reply_ratio` | ratio | `replies / views` |
| T-5 | `threads_satisfaction` | 0-100 score | weighted composite of reply, repost, quote, and follower-gain rates |
| T-6 | `media_type_branch` | `(high, low)` thresholds | threshold pair by media type |
| T-7 | `share_rate` | ratio | `shares / views` |
| T-8 | `quote_to_reply_ratio` | ratio | `quotes / replies` |
| T-9 | `link_attachment_penalty` | multiplier | `0.7` if an external link exists, else `1.0` |

### `threads_satisfaction` weights

| Weight | Signal | Target |
|---:|---|---|
| 35% | reply ratio | 5% |
| 30% | repost rate | 3% |
| 20% | quote rate | 2% |
| 15% | follower gain rate | 1% |

Targets are intentionally aggressive and represent viral-post levels. Use the score for relative comparison across a similar account/topic set.

### `media_type_branch` thresholds

| `media_type` | High | Low | Notes |
|---|---:|---:|---|
| `TEXT_POST` | 180 | 70 | fast decay |
| `IMAGE` | 200 | 75 | medium decay |
| `VIDEO` | 220 | 80 | slower growth and longer tail |
| `CAROUSEL_ALBUM` | 210 | 78 | sustained engagement |
| default | 210 | 75 | fallback |

## Excluded formulas

These YouTube-style formulas are intentionally not implemented for Threads because the API does not expose the required data.

| Category | Excluded signals | Reason |
|---|---|---|
| Watch time | completion rate, average view percentage, retention satisfaction | Threads does not expose watch time or retention |
| Shorts/duration | `is_short`, shorts VPH, duration branch | Threads media type is not equivalent to Shorts/Long |
| Revenue | RPM proxy, revenue estimate, seasonal adjust | Threads creator revenue data is not exposed |
| Keyword volume | demand, supply, gap score, competition, opportunity score, rank probability | no reliable keyword volume API |
| NLP | comment sentiment | requires external NLP pipeline and is outside pure API scoring |

## Labels and display

### Score bands

| Score | Label |
|---:|---|
| 80-100 | Excellent |
| 60-79 | Good |
| 40-59 | Average |
| 20-39 | Below Avg |
| 0-19 | Poor |

### Alert levels

| Modified z-score | Label | Suggested action |
|---:|---|---|
| `> 5.0` | Viral | immediate review |
| `> 3.5` | Surge | alert |
| `> 3.0` | Trending | watch closely |
| `> 2.0` | Watch | monitor |
| otherwise | None | no alert |

### Display rules

| Value type | Format | Example |
|---|---|---|
| ratio | multiply by 100 | `0.042` -> `4.2%` |
| score | round to integer plus label | `56` -> `56 Average` |
| large number | abbreviate K/M | `12400` -> `12.4K` |
| z-score | one decimal plus alert level | `4.2` -> `4.2 Surge` |
| velocity | one decimal per hour | `12.5` -> `12.5 reposts/h` |
