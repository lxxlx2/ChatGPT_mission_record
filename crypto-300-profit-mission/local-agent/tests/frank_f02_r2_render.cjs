"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

class Element {
  constructor(tag = "div") {
    this.tagName = tag;
    this.children = [];
    this.textContent = "";
    this.className = "";
    this.value = "";
    this.handlers = {};
    this.disabled = false;
  }
  get firstChild() { return this.children[0] || null; }
  append(...nodes) { this.children.push(...nodes); }
  removeChild(node) {
    const index = this.children.indexOf(node);
    assert.ok(index >= 0);
    this.children.splice(index, 1);
  }
  addEventListener(name, callback) { this.handlers[name] = callback; }
}
const ids = [
  "source-state", "source-explainer", "reload", "warning",
  "count-total", "count-positive", "count-zero", "count-unknown",
  "person", "wallet", "copy-wallet", "observed-time", "age",
  "slots", "source-hash", "copy-hash", "latest-attempt",
  "position-rows", "row-total", "mint-search", "state-filter"
];
const nodes = Object.fromEntries(ids.map(id => [id, new Element()]));
nodes["source-state"].parentElement = new Element();
nodes["state-filter"].value = "all";
const listeners = {};
const document = {
  createElement: tag => new Element(tag),
  getElementById: id => nodes[id] || null,
  addEventListener: (event, callback) => { listeners[event] = callback; }
};
const alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";
const mintList = [...alphabet.slice(0, 32)].map(c => c.repeat(32));
const original = mintList.map((mint, index) => ({
  mint, state: index === 0 ? "OPEN_ACCOUNT_NONZERO" :
    index === 1 ? "OPEN_ACCOUNT_ZERO" : "NO_OPEN_ACCOUNT_OBSERVED",
  observed_raw_amount: index === 0 ? "1200000" : index === 1 ? "0" : null,
  observed_quantity: index === 0 ? "1.2" : index === 1 ? "0" : null,
  token_account_count: index < 2 ? 1 : null
}));
const stamp = "2026-10-14T15:54:15.873036+00:00";
const base = () => ({
  kind: "F02_RESEARCH_ARCHIVED_OWNER_POSITIONS",
  schema_version: 1, person_id: "frank", wallet: "4".repeat(32),
  wallet_binding_role: "RESEARCH_ONLY", target_mint_count: 32,
  mints: original,
  slot_min: 456895319, slot_max: 456895320,
  verified_full_wire_capture_sha256: "a".repeat(64),
  latest_capture_sha256: "a".repeat(64),
  latest_attempt_capture_sha256: "a".repeat(64),
  source_observation_status: "BOTH_PROGRAMS_OBSERVED_NON_ATOMIC",
  latest_attempt_source_status: "BOTH_PROGRAMS_OBSERVED_NON_ATOMIC",
  latest_attempt_observed_at_utc: stamp,
  capture_observed_at_utc: stamp, capture_age_seconds: 20,
  max_age_seconds: 300,
  capture_fresh: true, archive_observation_usable: true,
  readiness: "FRESH_VERIFIED_ARCHIVED_OBSERVATION"
});
let response = base();
let calls = 0;
// Deterministic virtual time: a loaded source must expire without an API
// response, including when background timers are suspended.
let elapsedMs = 0;
let nextTimerId = 1;
const pendingTimers = new Map();
const NativeDate = Date;
class ClockDate extends NativeDate {
  static now() { return 1800000000000 + elapsedMs; }
}
const performance = {now: () => elapsedMs};
function setTimeoutFake(callback, delay) {
  const id = nextTimerId++;
  pendingTimers.set(id, {callback, due: elapsedMs + delay});
  return id;
}
function clearTimeoutFake(id) { pendingTimers.delete(id); }
function advance(ms, fireTimers = true) {
  elapsedMs += ms;
  if (!fireTimers) return;
  for (const [id, entry] of [...pendingTimers.entries()]) {
    if (elapsedMs >= entry.due) {
      pendingTimers.delete(id);
      entry.callback();
    }
  }
}
const window = {handlers:{}, addEventListener(name, callback) { this.handlers[name] = callback; }};
const writes = [];
const navigator = {clipboard:{writeText:async value => writes.push(value)}};
const context = {window, document, navigator, Date: ClockDate,
  performance, setTimeout: setTimeoutFake, clearTimeout: clearTimeoutFake,
  fetch:async (route, opts) => {
    assert.equal(route, "/api/research/positions");
    assert.equal(opts.cache, "no-store");
    assert.equal(opts.credentials, "omit");
    calls++;
    return {ok:true,json:async () => response};
  }};
const script = fs.readFileSync(path.join(__dirname, "../scripts/frank_f02_web/positions.js"), "utf8");
vm.runInNewContext(script, context, {filename:"positions.js"});
const {validated, safeObservation} = window.FrankF02Contract;
assert.equal(validated(base()), true);
assert.equal(safeObservation(base()), true);
const wait = () => new Promise(resolve => setImmediate(resolve));
async function run() {
  listeners.DOMContentLoaded();
  await wait();
  assert.equal(calls, 1);
  assert.equal(nodes["count-positive"].textContent, "1");
  assert.equal(nodes["count-zero"].textContent, "1");
  assert.equal(nodes["count-unknown"].textContent, "0");
  assert.equal(nodes["position-rows"].children.length, 32);
  assert.equal(nodes["position-rows"].children[0].children[2].textContent, "1.2");
  assert.equal(nodes["position-rows"].children[1].children[2].textContent, "0");
  assert.equal(nodes["position-rows"].children[2].children[2].textContent, "—");
  const copy = nodes["position-rows"].children[0].children[4].children[0].children[0];
  await copy.handlers.click();
  await wait();
  assert.equal(writes[0], mintList[0]);
  response = {...base(),readiness:"STALE_ARCHIVED_SOURCE",
    archive_observation_usable:false,capture_fresh:false,capture_age_seconds:7397,
    mints:original.map(row=>({...row,state:"SOURCE_UNAVAILABLE",
      observed_raw_amount:null,observed_quantity:null,token_account_count:null}))};
  await nodes.reload.handlers.click();
  await wait();
  assert.equal(nodes["count-unknown"].textContent, "32");
  assert.equal(nodes["position-rows"].children[0].children[2].textContent, "—");
  assert.equal(nodes["source-state"].textContent, "来源已过期");
  response = {...base(),latest_attempt_source_status:"PARTIAL_SOURCE"};
  assert.equal(safeObservation(response), false);
  await nodes.reload.handlers.click();
  await wait();
  assert.equal(nodes["source-state"].textContent, "来源信息不一致");
  assert.equal(nodes["count-positive"].textContent, "0");
  assert.equal(nodes["position-rows"].children[0].children[2].textContent, "—");
  response = base();
  await nodes.reload.handlers.click();
  await wait();
  nodes["mint-search"].value = mintList[0].slice(0,8);
  nodes["mint-search"].handlers.input();
  assert.equal(nodes["position-rows"].children.length, 1);
  nodes["mint-search"].value = "";
  nodes["mint-search"].handlers.input();
  nodes["state-filter"].value = "OPEN_ACCOUNT_NONZERO";
  nodes["state-filter"].handlers.change();
  assert.equal(nodes["position-rows"].children.length, 1);
  assert.equal(nodes["position-rows"].children[0].children[2].textContent, "1.2");
  assert.ok(calls >= 4);
  response = {...base(),capture_age_seconds:1,max_age_seconds:5};
  await nodes.reload.handlers.click();
  await wait();
  const callsBeforeTTL = calls;
  nodes["state-filter"].value = "all";
  nodes["state-filter"].handlers.change();
  assert.equal(nodes["position-rows"].children[0].children[2].textContent, "1.2");
  assert.equal(nodes["source-state"].textContent, "来源有效的归档观察");
  // API would become stale after five seconds. At three seconds the
  // conservative one-shot deadline must already hide balances.
  advance(3500);
  assert.equal(calls, callsBeforeTTL);
  assert.equal(nodes["source-state"].textContent, "来源已过期");
  assert.equal(nodes["count-positive"].textContent, "0");
  assert.equal(nodes["count-zero"].textContent, "0");
  assert.equal(nodes["count-unknown"].textContent, "32");
  assert.equal(nodes["position-rows"].children[0].children[2].textContent, "—");
  assert.equal(nodes["position-rows"].children[0].children[3].textContent, "—");
  assert.ok(nodes["age"].textContent.includes("4 秒前"));
  nodes["state-filter"].value = "OPEN_ACCOUNT_NONZERO";
  nodes["state-filter"].handlers.change();
  assert.equal(nodes["position-rows"].children.length, 1);
  assert.equal(nodes["position-rows"].children[0].children[0].textContent, "没有符合条件的研究目标");

  // Background throttle: even with the timeout unscheduled, returning to
  // a visible tab and interacting must fail closed immediately.
  response = {...base(),capture_age_seconds:1,max_age_seconds:5};
  nodes["state-filter"].value = "all";
  await nodes.reload.handlers.click();
  await wait();
  assert.equal(nodes["count-positive"].textContent, "1");
  advance(8000, false);
  document.visibilityState = "visible";
  listeners.visibilitychange();
  assert.equal(nodes["source-state"].textContent, "来源已过期");
  assert.equal(nodes["count-unknown"].textContent, "32");
  assert.equal(nodes["position-rows"].children[0].children[2].textContent, "—");
  assert.equal(calls, callsBeforeTTL + 1);
  process.stdout.write("F02_R2_NODE_RENDER=PASS: real loaded-source TTL expiry, background visibility, fresh, stale, metadata conflict, filters, copy\n");
}
run().catch(error => {console.error(error);process.exitCode=1});
