# Explosion Focus Scoring Logic (SaaS 3-Phase Separation)

This logic focuses on finding **relative explosion (z-score)** that exceeds an account's average weight class, not absolute numbers (Global Trend). Red ocean is treated as a **demand accelerator**, not a filter.

> **Platform**: Threads Graph API v1.0 (2024).
> The algorithm is source-agnostic — it reads only `views / hours_since_post / author baseline`.

## [Phase 1] Post Explosion Score (z-VPH)

* **Core Metric:** Relative z-VPH (Views Per Hour Z-score)
* **Description:** Measures how many standard deviations above the author's usual VPH a post currently sits.
* **Formula:**
  ```
  z_vph = (current_vph - author_avg_vph) / author_std_vph
  ```
* **Threads input fields:** `views` (Media Insights) + `timestamp` (Media Fields) → VPH;
  aggregate across author's recent posts for `author_avg_vph` / `author_std_vph`.
* **Open Research Questions:**
  - Small accounts (avg 10-20 views) can produce deformed z-scores when a post hits 100 views
  - Need optimal correction: minimum VPH threshold? Log scaling? Bayesian smoothing?
  - **autoresearch task:** Find the best correction formula to prevent small-account z-score inflation while preserving genuine explosion signals

## [Phase 2] Red Ocean Multiplier

* **Core Metric:** Topic Saturation Index as a multiplicative weight
* **Description:** If a post shows high z-VPH despite being on a saturated (red ocean) hashtag/topic, this proves explosive demand. Apply bonus multiplier.
* **Formula:**
  ```
  Phase2_Score = Phase1_Score * (1 + (topic_saturation_index * weight))
  ```
* **Threads input:** Hashtag frequency across recent 7-day window (count of posts under the same `topic_tag` or top hashtag). No keyword-volume API is available — saturation is derived from observed post counts.
* **Open Research Questions:**
  - Maximum cap needed to prevent runaway scores (e.g., cap at 1.5x?)
  - What cap value yields highest hit-rate in backtesting?
  - **autoresearch task:** Test optimal cap values (1.2x, 1.5x, 2.0x) against historical data to find best precision/recall balance

## [Phase 3] Usability & SaaS Output Separation

* **Core Metric:** Benchmarking suitability (imitability score)
* **Description:** Never mix post score and account score. Output must be separated into 3 independent JSON fields:
  1. Post burst score (pure explosion)
  2. Account baseline (foundation strength)
  3. Usability flag (difficulty for us to replicate this topic)

* **Target Output Schema:**
  ```json
  {
    "post_burst_score": 85,
    "red_ocean_multiplier": 1.2,
    "final_score": 102,
    "usability_flag": "HIGH"
  }
  ```

## Decision Log

| Dimension | Global Trend alternative | Our Choice (Explosion Focus) | Reason |
|-----------|------------------------------|------------------------------|--------|
| Core metric | Absolute VPH (market speed) | Relative z-VPH (account-relative burst) | "Explosion" = outperforming your own weight class, z-score captures this |
| Red ocean | Filter out (exclude) | Accelerator (multiply) | Viral in red ocean = proven demand, reward it |
| Architecture | Single unified score | 3-phase separation (post/account/usability) | Maintainability + SaaS extensibility, clear data pipeline |
| Platform | YouTube (watch_time/retention) | Threads (reposts/quotes/shares) | YouTube's retention signals unavailable via Threads API — replaced with reposts/quotes/shares as viral proxies |
