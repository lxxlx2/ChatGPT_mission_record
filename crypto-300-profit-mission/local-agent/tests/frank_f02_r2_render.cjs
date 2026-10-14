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
const window = {};
const writes = [];
const navigator = {clipboard:{writeText:async value => writes.push(value)}};
const context = {window, document, navigator,
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
  process.stdout.write("F02_R2_NODE_RENDER=PASS: fresh, stale, equal-UTC inconsistency, filters, copy\n");
}
run().catch(error => {console.error(error);process.exitCode=1});
