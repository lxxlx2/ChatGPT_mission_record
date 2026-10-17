'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const src = fs.readFileSync(
  'mission_agent/mission_control/static/frank_source_context.js', 'utf8'
);
const sandbox = {console};
vm.runInNewContext(src, sandbox, {filename: 'frank_source_context.js'});
const render = sandbox.FrankSourceContextUI.renderModel;
const A = 'So11111111111111111111111111111111111111112';
const B = 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v';
const now = 1792230000;
const doc = (rows) => ({
  schema_version: 1,
  kind: 'FRANK_CURRENT_F01_WITH_A05_RESEARCH_CONTEXT',
  candidate_count: rows.length,
  candidates: rows,
  combined_trade_permission: false,
  archive_is_live_wallet_portfolio: false,
  upstream: {f01: 'SOURCE_READ', f02: 'SOURCE_READ', c02: 'NOT_QUERIED'},
  f01_valid_until_epoch: now + 8,
});
const row = (mint, state, quantity, review) => ({
  person_id: 'frank', mint,
  source_signal_id: 'source-' + mint,
  f01_decision: 'BUY',
  wallet_observation_state: state,
  observed_quantity: quantity,
  observation_at_utc: '2026-10-17T00:00:00Z',
  review_required_reason: review,
  archived_source_only: true,
  current_wallet_position_verified: false,
  historical_sale_confirmed: false,
  may_trade_based_on_combination: false,
});
const REVIEW = 'F01_SIGNAL_VS_ARCHIVED_WALLET_REQUIRES_REVIEW';

const zero = doc([row(A, 'OPEN_ACCOUNT_ZERO', '0.000000', REVIEW)]);
const rendered = render(zero, new Set([A]), now);
assert.match(rendered, /需要复核/);
assert.match(rendered, /0\.000000/);
assert.match(rendered, /不代表已卖出/);
assert.match(rendered, /F01 资格剩余约 8 秒/);
assert.doesNotMatch(rendered, /当前实时仓位已确认/);

const positive = doc([row(A, 'OPEN_ACCOUNT_NONZERO', '123.000000', null)]);
assert.match(render(positive, new Set([A]), now), /123\.000000/);
assert.doesNotMatch(render(positive, new Set([A]), now), /需要复核/);
assert.match(render(positive, new Set([B]), now), /尚未匹配/);

const unobserved = doc([row(A, 'NO_OPEN_ACCOUNT_OBSERVED', null, REVIEW)]);
assert.match(render(unobserved, new Set([A]), now), /未观察到开放账户/);
assert.match(render(unobserved, new Set([A]), now), /需要复核/);
assert.doesNotMatch(render(unobserved, new Set([A]), now), /0\.000000/);
assert.match(render(doc([row(A, 'SOURCE_UNAVAILABLE', null, null)]),
  new Set([A]), now), /余额未知/);

const multiple = doc([
  row(A, 'OPEN_ACCOUNT_NONZERO', '123.000000', null),
  row(B, 'OPEN_ACCOUNT_ZERO', '0.000000', REVIEW)
]);
const visibleA = render(multiple, new Set([A]), now);
assert.match(visibleA, /123\.000000/);
assert.doesNotMatch(visibleA, /0\.000000/);
const visibleB = render(multiple, new Set([B]), now);
assert.match(visibleB, /0\.000000/);
assert.doesNotMatch(visibleB, /123\.000000/);

assert.match(render(zero, new Set([A]), now + 8), /已过期/);
assert.doesNotMatch(render(zero, new Set([A]), now + 8), /0\.000000/);
assert.match(render(zero, new Set([A]), now + 200), /已过期/);
assert.match(render({...zero, f01_valid_until_epoch: null},
  new Set([A]), now), /已过期/);
assert.match(render({...zero, combined_trade_permission: true},
  new Set([A]), now), /来源未接入/);
assert.match(render({...zero, upstream: {f01: 'SOURCE_UNAVAILABLE'}},
  new Set([A]), now), /来源未接入/);
assert.match(render({...zero, candidate_count: 0},
  new Set([A]), now), /来源未接入/);
assert.match(render(doc([]), new Set(), now), /没有可跟候选/);

const duplication = doc([row(A, 'OPEN_ACCOUNT_ZERO', '0', REVIEW),
  row(A, 'OPEN_ACCOUNT_NONZERO', '10', null)]);
assert.match(render(duplication, new Set([A]), now), /候选身份或来源格式异常/);

const forged = doc([{
  ...row(A, 'OPEN_ACCOUNT_NONZERO', '42', null),
  source_signal_id: '<script>alert(1)</script>'
}]);
const sanitized = render(forged, new Set([A]), now);
assert.doesNotMatch(sanitized, /<script>/);
const forgedQuantity = doc([row(A, 'OPEN_ACCOUNT_NONZERO', '<img onerror=alert(1)>', null)]);
assert.match(render(forgedQuantity, new Set([A]), now), /余额精度证据异常/);
const forgedState = doc([{
  ...row(A, 'OPEN_ACCOUNT_NONZERO', '7', null),
  may_trade_based_on_combination: true
}]);
assert.match(render(forgedState, new Set([A]), now), /来源证明不完整/);
console.log('FRANK_SOURCE_CONTEXT_RENDER_PASS: exact-mint, no-trade, expiry and XSS guards');
