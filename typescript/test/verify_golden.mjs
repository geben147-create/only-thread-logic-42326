/**
 * Verify Threads TypeScript port matches Python golden_vectors.json.
 * Run: node --experimental-strip-types typescript/test/verify_golden.mjs
 */

import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import * as f from '../src/formulas.ts';

const __dirname = dirname(fileURLToPath(import.meta.url));
const golden = JSON.parse(
  readFileSync(join(__dirname, '..', '..', 'golden_vectors.json'), 'utf-8'),
);
const TOL = golden.tolerance ?? 1e-9;

const D = {
  modified_z: (v) => f.modifiedZ(v.x, v.values),
  modified_z_empty: (v) => f.modifiedZ(v.x, v.values),
  alert_level_viral: (v) => f.alertLevel(v.z_score),
  alert_level_surge: (v) => f.alertLevel(v.z_score),
  alert_level_trending: (v) => f.alertLevel(v.z_score),
  alert_level_watch: (v) => f.alertLevel(v.z_score),
  alert_level_none: (v) => f.alertLevel(v.z_score),
  surge_z_spike: (v) => f.surgeZ(v.today, v.rolling_window),
  surge_z_flat: (v) => f.surgeZ(v.today, v.rolling_window),
  z_vph_normal: (v) => f.zVph(v.current_vph, v.author_avg_vph, v.author_std_vph)[0],
  z_vph_small_dampened: (v) => f.zVph(v.current_vph, v.author_avg_vph, v.author_std_vph)[0],
  red_ocean_blue: (v) => f.redOceanMultiplier(v.topic_saturation),
  red_ocean_capped: (v) => f.redOceanMultiplier(v.topic_saturation),
  final_score: (v) => f.finalScoreV1(v.z, v.multiplier),
  engagement_rate: (v) => f.engagementRate(v.likes, v.replies, v.views),
  like_ratio: (v) => f.likeRatio(v.likes, v.views),
  account_momentum: (v) => f.accountMomentum(
    v.views_30d, v.views_prev_30d, v.followers_30d_gained, v.followers_prev_30d_gained,
  ),
  views_per_follower: (v) => f.viewsPerFollower(v.avg_views_90d, v.total_followers),
  outlier_ratio: (v) => f.outlierRatio(v.post_views, v.account_avg_views),
  content_efficiency: (v) => f.contentEfficiency(v.views_30d, v.posts_30d),
  posting_consistency_regular: (v) => f.postingConsistency(v.post_timestamps_unix),
  audience_credibility_real: (v) => f.audienceCredibility(v.follower_engagement_rate),
  audience_credibility_suspicious: (v) => f.audienceCredibility(v.follower_engagement_rate),
  follower_conversion: (v) => f.followerConversion(v.followers_gained, v.views),
  account_health_score_perfect: (v) => f.accountHealthScore(
    v.engagement_rate_norm, v.posting_consistency_norm, v.views_per_follower_norm,
    v.content_efficiency_norm, v.posting_frequency_norm,
    v.follower_conversion_norm, v.audience_credibility_norm,
  ),
  growth_trigger_true: (v) => f.growthTrigger(v.growth_7d_ratio),
  growth_trigger_false: (v) => f.growthTrigger(v.growth_7d_ratio),
  repost_rate: (v) => f.repostRate(v.reposts, v.views),
  quote_rate: (v) => f.quoteRate(v.quotes, v.views),
  viral_velocity_24h_early: (v) => f.viralVelocity24h(v.reposts, v.hours_since_post),
  viral_velocity_24h_capped: (v) => f.viralVelocity24h(v.reposts, v.hours_since_post),
  reply_ratio: (v) => f.replyRatio(v.replies, v.views),
  threads_satisfaction_perfect: (v) => f.threadsSatisfaction(
    v.reply_ratio_val, v.repost_rate_val, v.quote_rate_val, v.follower_gain_rate,
  ),
  media_type_branch_text: (v) => f.mediaTypeBranch(v.media_type),
  media_type_branch_video: (v) => f.mediaTypeBranch(v.media_type),
  share_rate: (v) => f.shareRate(v.shares, v.views),
  quote_to_reply_ratio: (v) => f.quoteToReplyRatio(v.quotes, v.replies),
  link_attachment_penalty_with: (v) => f.linkAttachmentPenalty(v.link_attachment_url),
  link_attachment_penalty_without: (v) => f.linkAttachmentPenalty(v.link_attachment_url),
};

const eq = (a, b) => {
  if (typeof a === 'string' && typeof b === 'string') return a === b;
  if (typeof a === 'boolean' && typeof b === 'boolean') return a === b;
  if (Array.isArray(a) && Array.isArray(b)) {
    return a.length === b.length && a.every((x, i) => eq(x, b[i]));
  }
  if (typeof a === 'number' && typeof b === 'number') return Math.abs(a - b) < TOL;
  return a === b;
};

let pass = 0, fail = 0;
const failures = [];
for (const v of golden.vectors) {
  const fn = D[v.formula];
  if (!fn) { failures.push(`  MISSING: ${v.formula}`); fail++; continue; }
  try {
    const actual = fn(v.input);
    if (eq(actual, v.expected)) pass++;
    else { failures.push(`  MISMATCH ${v.formula}: exp=${JSON.stringify(v.expected)}, got=${JSON.stringify(actual)}`); fail++; }
  } catch (e) {
    failures.push(`  THREW ${v.formula}: ${e.message}`); fail++;
  }
}

console.log(`\ngolden_vectors: ${pass}/${pass + fail} passed (tolerance=${TOL})\n`);
if (fail > 0) {
  console.log('FAILURES:');
  for (const l of failures) console.log(l);
  process.exit(1);
}
console.log('✓ TypeScript port matches Python reference.');
