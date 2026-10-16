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
assert(html.includes("不跟（报价未核实）"));
assert(!html.includes("当前 $30 成交价</") || !html.includes(">0</strong>"),
  "wrong metrics zero cannot be displayed as executable quote");

ctx.rows=[{...conflicting,
 metrics:{execution_price_usdc:"0.012",price_impact_pct:"0.1",frank_latest_buy_price_usdc:"0.01"},
 validated_follow_quote:{execution_price_usdc:"0.012",price_impact_pct:"0.1"}}];
vm.runInContext("renderCandidates(rows)",ctx);
html=nodes.candidates.innerHTML;
assert(html.includes('class="badge buy"'));
assert(html.includes("0.012"));
assert(html.includes("0.1%"));

ctx.payload={status:"OK",summary:{total_observed:1},rows:[{
 mint:conflicting.mint,watch_state:"MODEL_OPEN",last_event_time:1800000000,
 snapshot_inventory_state:"NONZERO_AT_SLOT",snapshot_token_quantity:"12",
 snapshot_verified_slot:123456789
}]};
vm.runInContext("renderFrankWatchlist(payload)",ctx);
const watch=nodes["watch-rows"].innerHTML;
assert(!watch.includes("slot 123456789"),"formal F01 watchlist must not expose raw slot");
console.log("F01 quote projection matches current decision; formal watchlist Slot concealed PASS");
