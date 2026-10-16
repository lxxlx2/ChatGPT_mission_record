"use strict";
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");
const assert = require("node:assert/strict");
const script = fs.readFileSync(path.resolve(__dirname, "../mission_agent/mission_control/static/app.js"), "utf8");
const start = script.indexOf("function renderNotFollowed(");
const end = script.indexOf("\nfunction withinHours(", start);
assert(start >= 0 && end > start, "F01 renderNotFollowed source not found");
const nodes = {};
const node = name => nodes[name] ||= {innerHTML: "", textContent: "", hidden: false};
const excluded = [
  {decision: "BUY", mint: "SyntheticSoldMint", pattern: "MULTIPLE",
   exclusion_reason: "LATEST_ACTION_NOT_BUY", latest_side: "SELL"},
  {decision: "NO_BUY", mint: "SyntheticNoBuyMint", pattern: "MULTIPLE",
   exclusion_reason: "NOT_ACTIONABLE_DECISION", latest_side: "BUY"}
];
vm.runInNewContext(script.slice(start, end) + "\nrenderNotFollowed(excluded, 'OK');", {
  excluded, $: node,
  esc: text => String(text ?? "").replaceAll("<", "&lt;"),
  translated: (dictionary, key, fallback) => dictionary[key] || fallback,
  decisionLabel: {BUY: "可跟", NO_BUY: "不买"},
  patternLabel: {MULTIPLE: "多次强加仓"},
  followExclusionLabels: {LATEST_ACTION_NOT_BUY: "最近已卖出", NOT_ACTIONABLE_DECISION: "不构成跟单"},
  copyButton: () => "", researchLinks: () => ""
});
const result = nodes["not-followed"].innerHTML;
assert.equal(nodes["not-followed-count"].textContent, "2");
assert.equal(nodes["not-followed-panel"].hidden, false);
assert.equal((result.match(/class="badge no-buy"/g) || []).length, 2);
assert(!result.includes('class="badge buy"'), "excluded decision was wrongly styled as active BUY");
assert(result.includes("不跟"));
assert(result.includes("原模型判断：可跟 · 最近已卖出"));
assert(result.includes("原模型判断：不买 · 不构成跟单"));
console.log("F01 actual app.js excluded SELL/NO_BUY DOM badge semantics PASS");
