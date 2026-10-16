"use strict";
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");
const assert = require("node:assert/strict");

const root = path.resolve(__dirname, "..");
const src = fs.readFileSync(path.join(root, "mission_agent/mission_control/static/app.js"), "utf8").replace("\nrefresh();", "\n");
const nodes = {};
const node = id => nodes[id] ||= {
  innerHTML:"", textContent:"", hidden:false, value:"",
  addEventListener(){},
  classList:{toggle(){},add(){},remove(){}},
  querySelectorAll(){return []}
};
const ctx = {console, document:{getElementById:node,querySelectorAll(){return []},addEventListener(){}},
 window:{location:{hash:"#signals"},addEventListener(){}},history:{replaceState(){}},
 localStorage:{getItem(){return null},setItem(){}},setInterval(){},setTimeout(){},clearTimeout(){},
 fetch:async()=>({ok:true,json:async()=>({})})};
vm.createContext(ctx);
vm.runInContext(src,ctx);

const conflicting = {
 mint:"So11111111111111111111111111111111111111112",
 decision:"BUY",position_state:"OPEN",pattern:"MULTIPLE",latest_side:"BUY",
 metrics:{execution_price_usdc:"0",price_impact_pct:"NaN",frank_latest_buy_price_usdc:"0.01"},
 decision_quote:{status:"OK",route_exists:true,execution_price_usdc:"0.012",price_impact_pct:"0.1"},
 buy_count:1,sell_count:0
};
ctx.rows=[conflicting];
vm.runInContext("renderCandidates(rows)",ctx);
let html=nodes.candidates.innerHTML;
assert(!html.includes('class="badge buy"'),"unverified quote cannot make a green follow badge");
assert(html.includes('class="candidate-card decision-no-buy"'),
  "unverified BUY must not inherit the green decision-buy card border");
assert(!html.includes('class="candidate-card decision-buy"'));
assert(html.includes("不跟（报价未核实）"));
assert(/<span>当前 \$30 成交价<\/span>\s*<strong>暂无可用报价<\/strong>/.test(html),
  "current executable price must be unavailable, never 0 or NaN");
assert(/<span>预计价格冲击<\/span>\s*<strong>暂无可用报价<\/strong>/.test(html),
  "execution impact must be unavailable, never NaN%");
assert(!html.includes("NaN%") && !html.includes("0.00000000"));

ctx.rows=[{...conflicting,
 metrics:{execution_price_usdc:"0.012",price_impact_pct:"0.1",frank_latest_buy_price_usdc:"0.01"},
 validated_follow_quote:{execution_price_usdc:"0.012",price_impact_pct:"0.1"}}];
vm.runInContext("renderCandidates(rows)",ctx);
html=nodes.candidates.innerHTML;
assert(html.includes('class="badge buy"'));
assert(html.includes('class="candidate-card decision-buy"'));
assert(html.includes("0.012"));
assert(html.includes("0.1%"));

ctx.payload={status:"OK",summary:{total_observed:1},rows:[{
 mint:conflicting.mint,watch_state:"MODEL_OPEN",last_event_time:1800000000,
 snapshot_inventory_state:"NONZERO_AT_SLOT",snapshot_token_quantity:"12",
 snapshot_verified_slot:123456789
}]};
vm.runInContext("renderFrankWatchlist(payload)",ctx);
const watch=nodes["watch-rows"].innerHTML;
assert(!watch.includes("slot") && !watch.includes("123456789"),
  "formal F01 watchlist must not expose the Slot label or numeric value");
console.log("F01 quote projection matches current decision; formal watchlist Slot concealed PASS");
