'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { test } = require('node:test');

const js = fs.readFileSync(path.join(__dirname,
  '../mission_agent/mission_control/static/app.js'), 'utf8');
const first = js.indexOf('function verifiedF01SourceView(');
const last = js.indexOf('function renderF01History(', first);
assert.ok(first > 0 && last > first, 'actual F01 UI verifier must exist');
const now = 1800000000;
const context = {Date};
vm.createContext(context);
vm.runInContext(`const f01PageOpenedAtEpoch = ${now-100};
const f01FirstSeenKeys = new Set();
const f01ObservedLagSeconds = [];
` + js.slice(first, last) +
  '\nthis.verify = verifiedF01SourceView; this.observe = recordF01PageObservation; this.epoch = f01EventEpoch; this.excludedCount = f01ExcludedReasonCount;', context);
const verify = context.verify;
const row = Object.freeze({
  person_id:'frank', mint:'7VertkgF9KLhxxJXHX6uaWuoYZTP9LdGj2bWmVXVpump',
  episode_id:'E1', source_signal_id:'S1', latest_signature:'SIG1',
  latest_buy_at:now-4, latest_at:now-4, latest_side:'BUY', decision:'NO_BUY'
});
const doc = (overrides={}) => ({
  schema_version:2, status:'SOURCE_ONLY',
  scope:'FRANK_LOCAL_INDEX_SOURCE_ONLY_NO_EXECUTION_QUOTE',
  as_of_epoch:now-1, eligible:[], eligible_count:0,
  source_recent_count:1,
  source_recent:[{...row,f01_source_state:'RECENT_SOURCE_BUY_ONLY',
    execution_eligibility:'NOT_ASSESSED_USER_AMOUNT_MISSING'}],
  ...overrides,
});
test('source-only observation keeps NO_BUY historical decision, never execution',()=>{
  const out = verify(doc(),[row],now);
  assert.equal(out.recent.length,1);
  assert.equal(out.recent[0].decision,'NO_BUY');
  assert.equal(out.historical.length,0);
});
test('mismatched source, newer SELL and absent candidate fail closed',()=>{
  assert.equal(verify(doc(),[{...row,source_signal_id:'OTHER'}],now),null);
  assert.equal(verify(doc(),[{...row,latest_side:'SELL'}],now),null);
  assert.equal(verify(doc(),[{...row,decision:'BUY'}],now),null);
  assert.equal(verify(doc(),[{...row,position_state:'CLOSED'}],now),null);
  assert.equal(verify(doc(),[],now),null);
  assert.equal(verify(doc(),[row,row],now),null);
});
test('wrong schema, stale, future, missing or unexpected executable decision fail closed',()=>{
  for (const changed of [
    {schema_version:1},{status:'RUNTIME_UNAVAILABLE'},
    {status:'SOURCE_UNAVAILABLE'},
    {as_of_epoch:now-9},{as_of_epoch:now+1},
    {eligible:[row]}, {eligible_count:1},
    {source_recent_count:0},
    {source_recent:[{...doc().source_recent[0],execution_eligibility:'OK'}]},
    {source_recent:[{...doc().source_recent[0],f01_source_state:'ELIGIBLE'}]},
  ]) assert.equal(verify(doc(changed),[row],now),null);
  assert.equal(verify(null,[row],now),null);
});
test('historical rows remain visible even if no recent signal',()=>{
  const result = verify(doc({source_recent:[],source_recent_count:0}),[row],now);
  assert.equal(result.recent.length,0);
  assert.equal(result.historical.length,1);
});

test('missing stale exclusion category is a true zero when other reasons exist',()=>{
  const counts = context.excludedCount;
  assert.equal(counts({excluded_reason_counts:{MODEL_POSITION_NOT_OPEN:4}},
    'SOURCE_BUY_STALE_OR_UNVERIFIED'),0);
  assert.equal(counts({excluded_reason_counts:{}},
    'SOURCE_BUY_STALE_OR_UNVERIFIED'),0);
  assert.equal(counts({excluded_reason_counts:{SOURCE_BUY_STALE_OR_UNVERIFIED:3}},
    'SOURCE_BUY_STALE_OR_UNVERIFIED'),3);
});
test('invalid or missing reason-count map must remain unknown rather than fabricated zero',()=>{
  const counts = context.excludedCount;
  for (const x of [null,{}, {excluded_reason_counts:null},
      {excluded_reason_counts:[]},
      {excluded_reason_counts:{SOURCE_BUY_STALE_OR_UNVERIFIED:-1}},
      {excluded_reason_counts:{SOURCE_BUY_STALE_OR_UNVERIFIED:3.5}},
      {excluded_reason_counts:{SOURCE_BUY_STALE_OR_UNVERIFIED:'3'}}]) {
    assert.equal(counts(x,'SOURCE_BUY_STALE_OR_UNVERIFIED'),'未知');
  }
});

test('chain epoch parser handles numeric seconds and timezone-bearing timestamps only',()=>{
  assert.equal(context.epoch(now-1),now-1);
  assert.equal(context.epoch(String(now-1)),now-1);
  assert.equal(context.epoch(new Date((now-1)*1000).toISOString()),now-1);
  assert.equal(context.epoch('2026-10-28T08:00:00'),null);
  assert.equal(context.epoch('garbage'),null);
});
test('first-browser observation is counted once and clearly not index ingest time',()=>{
  const view={recent:[row],historical:[]};
  assert.match(context.observe(view,now),/初见样本 1 条/);
  assert.match(context.observe(view,now+2),/初见样本 1 条/);
  const historicBeforeOpen={...row,latest_signature:'older',latest_buy_at:now-120,latest_at:now-120};
  assert.match(context.observe({recent:[],historical:[historicBeforeOpen]},now+3),/初见样本 1 条/);
});
test('late FIRST observation of a post-open source BUY is detected from history',()=>{
  const late={...row,latest_signature:'fresh-but-late',latest_side:'BUY'};
  const result=context.observe({recent:[],historical:[late]},now+601);
  assert.match(result,/初见样本 2 条/);
  assert.match(result,/1 条超过10分钟/);
  assert.match(result,/不能拆分为纯索引延迟/);
});
