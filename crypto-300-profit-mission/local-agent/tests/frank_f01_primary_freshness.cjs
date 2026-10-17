'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const src=fs.readFileSync('mission_agent/mission_control/static/frank_f01_primary_freshness.js','utf8');
const A='So11111111111111111111111111111111111111112';
const B='EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v';
let clock=1792230000*1000;
const Clock=class extends Date{static now(){return clock}};
const action=(mint,id='signal-1',decision='BUY')=>({mint,person_id:'frank',source_signal_id:id,decision});
const watch={mint:B,person_id:'frank',source_signal_id:'watch-1',decision:'WAIT'};
const documentRows=[];
const cards=[];
const requests=[];
const timers=new Map();
let nextTimer=0, dispatched=0, visibleListener=null, countValue='0';
const following=(rows,age=1)=>({status:'OK',eligible:rows,eligible_count:rows.length,as_of_epoch:clock/1000-age});
const flush=()=>new Promise(resolve=>setImmediate(resolve));
const mkCard=(item)=>{
 const isBuy=item.decision==='BUY'||item.decision==='SMALL_BUY';
 const label=isBuy?(item.decision==='BUY'?'可跟':'小仓跟'):'等待';
 const card={className:'candidate-card decision-'+item.decision.toLowerCase().replaceAll('_','-'),dataset:{},badge:{className:'badge '+item.decision.toLowerCase(),textContent:label},conclusion:{textContent:'当前跟单结论：“'+label+'”'},mint:item.mint};
 card.classList={
  add(...names){const s=new Set(card.className.split(' '));names.forEach(n=>s.add(n));card.className=[...s].join(' ');},
  remove(...names){const s=new Set(card.className.split(' '));names.forEach(n=>s.delete(n));card.className=[...s].join(' ');}
 };
 card.querySelector=q=>q==='.candidate-head .badge'?card.badge:
   q==='.decision-reason > span'?card.conclusion:
   q==='.ca-full'?{textContent:card.mint}:null;
 return card;
};
const stats={querySelectorAll(q) {assert.equal(q,'.stat');return [{querySelector(q){return q==='span'?{textContent:'当前可跟候选'}:q==='strong'?{set textContent(v){countValue=v;},get textContent(){return countValue;}}:null;}}];}};
const holder={querySelectorAll(q){assert.equal(q,'.candidate-card');return cards;}};
const window={
 console,Date:Clock,
 renderCandidates(rows){cards.splice(0,cards.length,...rows.map(mkCard));documentRows.splice(0,documentRows.length,...rows);},
 document:{hidden:false,getElementById:q=>q==='candidates'?holder:q==='stats'?stats:null,
           addEventListener:(k,fn)=>{if(k==='visibilitychange')visibleListener=fn;}},
 Event:class Event{constructor(type){this.type=type;}},
 dispatchEvent(){dispatched++;},
 fetch:(url,opts)=>{assert.equal(url,'/api/follow-opportunities');assert.equal(opts.method,'GET');return new Promise((resolve,reject)=>requests.push({resolve,reject}));},
 setTimeout:(fn,ms)=>{const id=++nextTimer;timers.set(id,{fn,ms,active:true});return id;},
 clearTimeout:id=>{const t=timers.get(id);if(t)t.active=false;}
};
window.window=window;
vm.runInNewContext(src,window,{filename:'frank_f01_primary_freshness.js'});
const verify=window.FrankPrimaryF01Freshness.verifyRows;
assert.ok(verify([action(A)],following([action(A)]),clock/1000)>clock/1000);
assert.ok(verify([action(A),watch],following([action(A)]),clock/1000)>clock/1000);
assert.equal(verify([action(A),watch],following([]),clock/1000),null);
assert.equal(verify([action(A),watch],following([action(A,'other')]),clock/1000),null);
assert.equal(verify([action(A)],following([action(A,'signal-1','SMALL_BUY')]),clock/1000),null);
assert.equal(verify([action(A)],following([action(A)],9),clock/1000),null);
assert.equal(verify([watch],following([]),clock/1000),null);
const settle=async (rows)=>{const p=requests.shift();assert.ok(p,'expected fresh F01 request');p.resolve({ok:true,json:async()=>following(rows)});await flush();};
(async()=>{
  // One mixed historical BUY+WAIT, but empty verified F01 => BUY must stay masked,
  // while the WATCH label MUST stay WATCH, never overwritten as a BUY failure.
  window.renderCandidates([action(A),watch]);
  assert.match(cards[0].badge.textContent,/待核实/);
  assert.equal(cards[1].badge.textContent,'等待');
  await settle([]);
  assert.match(cards[0].badge.textContent,/待核实/);
  assert.equal(cards[1].badge.textContent,'等待');
  assert.equal(countValue,'待核实');
  assert.notEqual(cards[0].dataset.f01GuardState,'VERIFIED');

  // Mixed correctly approved fresh F01 => restore exactly one BUY, not two.
  window.renderCandidates([action(A),watch]);
  await settle([action(A)]);
  assert.equal(cards[0].badge.textContent,'可跟');
  assert.equal(cards[0].dataset.f01GuardState,'VERIFIED');
  assert.equal(cards[1].badge.textContent,'等待');
  assert.equal(countValue,'1');
  const exp=[...timers.values()].find(t=>t.active && t.ms > 6000);
  assert.ok(exp,'actual original-card expiry timer exists');
  // Same rows immediately rerender: original DOM remains verified without a
  // visible mask/restore flicker before a still-pending verification fetch.
  window.renderCandidates([action(A),watch]);
  assert.equal(cards[0].badge.textContent,'可跟');
  assert.equal(cards[1].badge.textContent,'等待');
  assert.equal(countValue,'1');
  await settle([action(A)]);
  clock+=9000;
  [...timers.values()].filter(t=>t.active).at(-1).fn();
  assert.equal(cards[0].dataset.f01GuardState,'UNVERIFIED');
  assert.doesNotMatch(cards[0].badge.textContent,/可跟/);
  assert.equal(cards[1].badge.textContent,'等待');
  assert.equal(countValue,'待核实');

  window.renderCandidates([action(A)]);
  await settle([action(A,'changed')]);
  assert.equal(cards[0].dataset.f01GuardState,'UNVERIFIED');

  window.renderCandidates([action(A,'old')]);
  const old=requests.shift();
  window.renderCandidates([action(B,'new')]);
  const newest=requests.shift();
  newest.resolve({ok:true,json:async()=>following([action(B,'new')])});
  await flush();
  assert.equal(cards[0].dataset.f01GuardState,'VERIFIED');
  old.resolve({ok:true,json:async()=>following([action(A,'old')])});
  await flush();
  assert.equal(cards[0].dataset.f01GuardState,'VERIFIED');
  assert.equal(cards[0].dataset.f01SourceSignalId,'new');

  window.renderCandidates([action(A)]);
  requests.shift().reject(new Error('OFFLINE'));
  await flush();
  assert.equal(cards[0].dataset.f01GuardState,'UNVERIFIED');

  window.renderCandidates([action(A)]);
  const pending=requests.shift();
  window.document.hidden=false;
  assert.ok(visibleListener);
  visibleListener();
  const foreground=requests.shift();
  foreground.resolve({ok:true,json:async()=>following([action(A)])});
  await flush();
  assert.equal(cards[0].dataset.f01GuardState,'VERIFIED');
  pending.resolve({ok:true,json:async()=>following([action(A,'old')])});
  await flush();
  assert.equal(cards[0].dataset.f01GuardState,'VERIFIED');
  assert.ok(dispatched>=5);
  console.log('FRANK_PRIMARY_F01_FRESHNESS_PASS: mixed fail-closed, action-only count, no-flicker, expiry, race, offline');
})().catch(e=>{console.error(e);process.exitCode=1;});
