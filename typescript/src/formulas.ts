/**
 * SOTDA Threads — 26 formulas (TypeScript port).
 * Zero runtime dependencies. Works in Node.js, Deno, Bun, Next.js,
 * React, browser. Target ES2022+.
 *
 * Mirrors sotda/formulas.py; passes golden_vectors.json at 1e-9 tolerance.
 */

// Helpers
function median(values: number[]): number {
  if (values.length === 0) return 0;
  const s = [...values].sort((a, b) => a - b);
  const n = s.length;
  return n % 2 === 1 ? s[Math.floor(n / 2)] : (s[n / 2 - 1] + s[n / 2]) / 2;
}
function mean(values: number[]): number {
  if (values.length === 0) return 0;
  return values.reduce((a, b) => a + b, 0) / values.length;
}
function stdev(values: number[]): number {
  if (values.length < 2) return 0;
  const m = mean(values);
  const sum = values.reduce((a, v) => a + (v - m) ** 2, 0);
  return Math.sqrt(sum / (values.length - 1));
}

// 🟢 Trend (3)
export function modifiedZ(x: number, values: number[]): number {
  if (values.length === 0) return 0;
  const med = median(values);
  const dev = values.map(v => Math.abs(v - med));
  let mad = median(dev);
  if (mad === 0) mad = 1.0;
  return (0.6745 * (x - med)) / mad;
}
export type AlertLevel = 'viral' | 'surge' | 'trending' | 'watch' | 'none';
export function alertLevel(z: number, growth7d = 0): AlertLevel {
  if (z > 5.0) return 'viral';
  if (z > 3.5 || growth7d > 2.0) return 'surge';
  if (z > 3.0 || growth7d > 1.0) return 'trending';
  if (z > 2.0 || growth7d > 0.5) return 'watch';
  return 'none';
}
export function surgeZ(today: number, rolling: number[]): number {
  if (rolling.length < 2) return 0;
  const m = mean(rolling);
  let s = stdev(rolling);
  if (s === 0) s = 1.0;
  return (today - m) / s;
}

// 🟢 Post (5)
export function zVph(
  currentVph: number, authorAvgVph: number, authorStdVph: number,
  minVphThreshold = 50, minStdFloor = 5,
): [number, string[]] {
  const corr: string[] = [];
  const effStd = Math.max(authorStdVph, minStdFloor);
  if (authorStdVph < minStdFloor) {
    corr.push(`std_floor_applied: ${authorStdVph.toFixed(2)} -> ${effStd.toFixed(2)}`);
  }
  const rawZ = (currentVph - authorAvgVph) / effStd;
  if (authorAvgVph < minVphThreshold) {
    const damp = Math.log1p(Math.abs(rawZ)) * (rawZ >= 0 ? 1 : -1);
    corr.push(`log_scaling_applied: raw_z=${rawZ.toFixed(2)} -> dampened_z=${damp.toFixed(2)}`);
    return [damp, corr];
  }
  return [rawZ, corr];
}
export function redOceanMultiplier(sat: number, weight = 0.5, cap = 1.5): number {
  if (cap < 1.0) throw new Error(`cap must be >= 1.0, got ${cap}`);
  return 1.0 + Math.min(sat * weight, cap - 1.0);
}
export function finalScoreV1(z: number, m: number, base = 50, scale = 50): number {
  return z * m * scale + base;
}
/** Threads: (likes + replies) / views */
export function engagementRate(likes: number, replies: number, views: number): number {
  if (views <= 0) return 0;
  return (likes + replies) / views;
}
export function likeRatio(likes: number, views: number): number {
  if (views <= 0) return 0;
  return likes / views;
}

// 🟢 Account (9)
export function accountMomentum(
  v30: number, vPrev: number, f30: number, fPrev: number,
): number {
  if (vPrev <= 0 || fPrev <= 0) return 0;
  return (v30 / vPrev) * (f30 / fPrev);
}
export function viewsPerFollower(avgViews90d: number, totalFollowers: number): number {
  if (totalFollowers <= 0) return 0;
  return avgViews90d / totalFollowers;
}
export function outlierRatio(postViews: number, avgViews: number): number {
  if (avgViews <= 0) return 0;
  return postViews / avgViews;
}
export function contentEfficiency(views30d: number, posts30d: number): number {
  if (posts30d <= 0) return 0;
  return views30d / posts30d;
}
export function postingConsistency(timestamps: number[]): number {
  if (timestamps.length < 3) return 0;
  const s = [...timestamps].sort((a, b) => a - b);
  const iv: number[] = [];
  for (let i = 0; i < s.length - 1; i++) iv.push(s[i + 1] - s[i]);
  if (iv.length < 2) return 0;
  const m = mean(iv);
  if (m <= 0) return 0;
  return 1 / (1 + stdev(iv) / m);
}
export type CredibilityLevel = 'REAL' | 'SUSPICIOUS';
export function audienceCredibility(er: number, threshold = 0.05): CredibilityLevel {
  return er >= threshold ? 'REAL' : 'SUSPICIOUS';
}
export function followerConversion(gained: number, views: number): number {
  if (views <= 0) return 0;
  return gained / views;
}
function clamp(v: number, lo = 0, hi = 100): number {
  return Math.max(lo, Math.min(v, hi));
}
export function normalizeEngagementRate(er: number, target = 0.05): number {
  if (er <= 0) return 0;
  return clamp((er / target) * 100);
}
export function normalizePostingConsistency(c: number): number {
  return clamp(c * 100);
}
export function normalizeViewsPerFollower(vpf: number, target = 0.10): number {
  if (vpf <= 0) return 0;
  return clamp((vpf / target) * 100);
}
export function normalizeContentEfficiency(eff: number, target = 10_000): number {
  if (eff <= 0) return 0;
  return clamp((eff / target) * 100);
}
export function normalizePostingFrequency(posts30d: number, target = 30): number {
  if (posts30d <= 0) return 0;
  return clamp((posts30d / target) * 100);
}
export function normalizeFollowerConversion(conv: number, target = 0.02): number {
  if (conv <= 0) return 0;
  return clamp((conv / target) * 100);
}
export function normalizeAudienceCredibility(v: CredibilityLevel): number {
  return v === 'REAL' ? 100 : 30;
}
export function accountHealthScore(
  erN: number, pcN: number, vpfN: number, ceN: number,
  pfN: number, fcN: number, acN: number,
): number {
  return 0.25 * erN + 0.15 * pcN + 0.15 * vpfN + 0.15 * ceN
       + 0.10 * pfN + 0.10 * fcN + 0.10 * acN;
}
export function growthTrigger(ratio: number, threshold = 2.0): boolean {
  return ratio > threshold;
}

// 🔵 Threads-specific (9)
export function repostRate(reposts: number, views: number): number {
  if (views <= 0) return 0;
  return reposts / views;
}
export function quoteRate(quotes: number, views: number): number {
  if (views <= 0) return 0;
  return quotes / views;
}
export function viralVelocity24h(reposts: number, hoursSincePost: number): number {
  const h = Math.min(Math.max(hoursSincePost, 1.0), 24.0);
  return reposts / h;
}
export function replyRatio(replies: number, views: number): number {
  if (views <= 0) return 0;
  return replies / views;
}
export function threadsSatisfaction(
  reply: number, repost: number, quote: number, followerGain: number,
): number {
  const r  = reply > 0       ? Math.min((reply  / 0.05) * 100, 100) : 0;
  const p  = repost > 0      ? Math.min((repost / 0.03) * 100, 100) : 0;
  const q  = quote > 0       ? Math.min((quote  / 0.02) * 100, 100) : 0;
  const f  = followerGain > 0? Math.min((followerGain / 0.01) * 100, 100) : 0;
  return 0.35 * r + 0.30 * p + 0.20 * q + 0.15 * f;
}
export type MediaType = 'TEXT_POST' | 'IMAGE' | 'VIDEO' | 'CAROUSEL_ALBUM';
export function mediaTypeBranch(mt: string): [number, number] {
  const t: Record<string, [number, number]> = {
    TEXT_POST: [180, 70], IMAGE: [200, 75],
    VIDEO: [220, 80], CAROUSEL_ALBUM: [210, 78],
  };
  return t[mt] ?? [210, 75];
}
export function shareRate(shares: number, views: number): number {
  if (views <= 0) return 0;
  return shares / views;
}
export function quoteToReplyRatio(quotes: number, replies: number): number {
  if (replies <= 0) return 0;
  return quotes / replies;
}
export function linkAttachmentPenalty(linkAttachmentUrl: string | null | undefined): number {
  return linkAttachmentUrl ? 0.7 : 1.0;
}
