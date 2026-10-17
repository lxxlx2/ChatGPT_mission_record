'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const script=fs.readFileSync('mission_agent/mission_control/static/frank_f01_primary_freshness.js','utf8');
const A='So11111111111111111111111111111111111111112';
const B='EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v';
let clock=1792230000*1000;
const FakeDate=class extends Date {static now(){return clock;}};
const row=(mint,id='signal-1',decision='BUY')=>({mint,person_id:'frank',source_signal_id:id,decision});
const follow=(rowSet, secondsOld=1)=>({
  status:'OK',eligible:rowSet,eligible_count:rowSet.length,
  as_of_epoch:clock/1000-secondsOld
});
const requests=[];
const timers=new Map();
let nextTimer=0, pageCards=[],visibilityListener=null;
let notices=0;
const makeCard=()=>{
  const card={
    className:'candidate-card decision-buy',dataset:{},
    badge:{className:'badge buy',textContent:'可跟'},
    conclusion:{textContent:'当前跟单结论：“可跟”'},
  };
  card.classList={
    add(...names){let a=new Set(card.className.split(' '));names.forEach(n=>a.add(n));card.className=[...a].join(' ');},
    remove(...names){let a=new Set(card.className.split(' '));names.forEach(n=>a.delete(n));card.className=[...a].join(' ');}
  };
  card.querySelector=(q)=>q==='.candidate-head .badge'?card.badge:q==='.decision-reason > span'?card.conclusion:null;
  return card;
};
const container={querySelectorAll(q) {
  assert.equal(q,'.candidate-card');
  return pageCards;
}};
const scope={
  console, Date:FakeDate,
  renderCandidates: (rows)=>{
    pageCards=rows.map(()=>makeCard());
  },
  document:{
    hidden:false,
    getElementById: (q)=>q==='candidates'?container:null,
    addEventListener:(q,fn)=>{if(q==='visibilitychange')visibilityListener=fn;}
  },
  Event:class Event{constructor(type){this.type=type;}},
  dispatchEvent:()=>{notices++;},
  fetch:(path,options)=>{
    assert.equal(path,'/api/follow-opportunities');
    assert.equal(options.method,'GET');
    return new Promise((resolve,reject)=>requests.push({resolve,reject}));
  },
  setTimeout:(fn,delay)=>{const id=++nextTimer;timers.set(id,{fn,delay,active:true});return id;},
  clearTimeout:(id)=>{if(timers.has(id))timers.get(id).active=false;}
};
scope.window=scope;
vm.runInNewContext(script,scope,{filename:'frank_f01_primary_freshness.js'});
const verify=scope.FrankPrimaryF01Freshness.verifyRows;
assert.ok(verify([row(A)],follow([row(A)]),clock/1000)>clock/1000);
assert.equal(verify([row(A)],follow([row(A,'other')]),clock/1000),null);
assert.equal(verify([row(A)],follow([row(A,'signal-1','SMALL_BUY')]),clock/1000),null);
assert.equal(verify([row(A)],follow([row(A)],9),clock/1000),null);
assert.equal(verify([row(A)],{...follow([row(A)]),status:'RUNTIME_UNAVAILABLE'},clock/1000),null);

const flush=()=>new Promise(resolve=>setImmediate(resolve));
(async()=>{
  scope.renderCandidates([row(A)]);
  assert.match(pageCards[0].badge.textContent,/待核实/);
  requests.shift().resolve({ok:true,json:async()=>follow([row(A)])});
  await flush();
  assert.equal(pageCards[0].dataset.f01GuardState,'VERIFIED');
  assert.equal(pageCards[0].badge.textContent,'可跟');
  const timer=[...timers.values()].find(t=>t.active);
  assert.ok(timer && timer.delay>0,'expiry timer should be active');
  clock+=9000;
  timer.fn();
  assert.equal(pageCards[0].dataset.f01GuardState,'UNVERIFIED');
  assert.doesNotMatch(pageCards[0].badge.textContent,/可跟/);
  assert.doesNotMatch(pageCards[0].conclusion.textContent,/“可跟”/);

  clock+=1000;
  scope.renderCandidates([row(A)]);
  requests.shift().resolve({ok:true,json:async()=>follow([row(A,'changed-id')])});
  await flush();
  assert.equal(pageCards[0].dataset.f01GuardState,'UNVERIFIED');

  scope.renderCandidates([row(A,'old')]);
  const old=requests.shift();
  scope.renderCandidates([row(B,'new')]);
  const latest=requests.shift();
  latest.resolve({ok:true,json:async()=>follow([row(B,'new')])});
  await flush();
  assert.equal(pageCards[0].dataset.f01GuardState,'VERIFIED');
  assert.equal(pageCards[0].dataset.f01SourceSignalId,'new');
  old.resolve({ok:true,json:async()=>follow([row(A,'old')])});
  await flush();
  assert.equal(pageCards[0].dataset.f01GuardState,'VERIFIED');
  assert.equal(pageCards[0].dataset.f01SourceSignalId,'new');

  scope.renderCandidates([row(A)]);
  requests.shift().reject(new Error('OFFLINE'));
  await flush();
  assert.equal(pageCards[0].dataset.f01GuardState,'UNVERIFIED');

  clock+=500;
  scope.renderCandidates([row(A)]);
  const pending=requests.shift();
  assert.equal(pageCards[0].dataset.f01GuardState,'UNVERIFIED');
  assert.ok(visibilityListener);
  scope.document.hidden=false;
  visibilityListener();
  const foreground=requests.shift();
  foreground.resolve({ok:true,json:async()=>follow([row(A)])});
  await flush();
  assert.equal(pageCards[0].dataset.f01GuardState,'VERIFIED');
  pending.resolve({ok:true,json:async()=>follow([row(A,'stale')])});
  await flush();
  assert.equal(pageCards[0].dataset.f01GuardState,'VERIFIED');
  assert.ok(notices>=4);
  console.log('FRANK_PRIMARY_F01_FRESHNESS_PASS: true expiry, failure, source identity, race, foreground');
})().catch(e=>{console.error(e);process.exitCode=1;});
