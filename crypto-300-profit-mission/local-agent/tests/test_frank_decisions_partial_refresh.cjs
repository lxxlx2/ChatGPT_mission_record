'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const vm = require('node:vm');

const app = fs.readFileSync(path.resolve(__dirname, '../mission_agent/mission_control/static/app.js'), 'utf8');
function section(begin, end) {
  const from = app.indexOf(begin);
  const to = app.indexOf(end, from + begin.length);
  assert(from >= 0 && to > from, 'missing real product source: ' + begin);
  return app.slice(from, to);
}
const getCode = section('async function get(path) {', 'function renderRuntime(runtime, control) {');
const refreshCode = section('async function refresh() {', '\nrefresh();');

const endpoints = {
  '/api/runtime': {status:'LIVE'},
  '/api/control-health': {status:'LIVE'},
  '/api/candidates': [{mint:'A'.repeat(32),position_state:'OPEN',latest_at:123}],
  '/api/trades': [],
  '/api/review-activity': [],
  '/api/decisions': [{decision:'WAIT'}],
  '/api/coverage': {status:'OBSERVED'},
  '/api/frank-observed-watchlist': {status:'OBSERVED',rows:[],summary:{}},
};

(async()=>{
  const calls = [];
  const failed = new Set(['/api/decisions']);
  const server = http.createServer((req,res)=>{
    calls.push({method:req.method,path:req.url});
    if(req.method !== 'GET' || !(req.url in endpoints)) {
      res.writeHead(405,{'Content-Type':'application/json'}).end('{}');
      return;
    }
    res.writeHead(failed.has(req.url)?503:200,{'Content-Type':'application/json'});
    res.end(JSON.stringify(failed.has(req.url)?{error:'SOURCE_UNAVAILABLE'}:endpoints[req.url]));
  });
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  try {
    const origin = 'http://127.0.0.1:' + server.address().port;
    const elements = {
      runtime:{innerHTML:'',className:''},
      decisions:{innerHTML:''},
      updated:{textContent:''},
    };
    const rendered = [];
    const ctx = {
      Date,
      fetch:(url, opts)=>fetch(origin+url,opts),
      $:id=>elements[id],
      esc: x=>String(x),
      withinHours:()=>true,
      renderRuntime:(runtime, control)=>{
        elements.runtime.className = 'runtime live';
        elements.runtime.innerHTML = 'Frank监控正常';
        rendered.push(['runtime',runtime.status]);
      },
      renderStats:()=>rendered.push(['stats']),
      renderCoverage:()=>rendered.push(['coverage']),
      renderFrankWatchlist:()=>rendered.push(['watch']),
      renderCandidates:(x)=>rendered.push(['candidates',x.length]),
      renderArchivedCandidates:()=>rendered.push(['archived']),
      renderEnded:()=>rendered.push(['ended']),
      renderTrades:()=>rendered.push(['trades']),
      renderReviewActivity:()=>rendered.push(['review']),
      renderDecisions:(rows)=>{
        rendered.push(['decisions',rows.length]);
        elements.decisions.innerHTML='历史判断实际数量:'+rows.length;
      },
      FrankCandidateSections:{split:items=>({current:items,archived:[]})},
    };
    vm.createContext(ctx);
    vm.runInContext(getCode + '\n' + refreshCode,ctx);
    assert.equal(typeof ctx.refresh,'function');
    await ctx.refresh();
    assert(elements.runtime.innerHTML.includes('Frank监控正常'));
    assert(!elements.runtime.className.includes('offline'));
    assert(elements.decisions.innerHTML.includes('暂时无法读取'));
    assert(elements.decisions.innerHTML.includes('/api/decisions'));
    for(const name of ['runtime','stats','coverage','watch','candidates','archived','ended','trades','review']){
      assert(rendered.some(row=>row[0]===name), 'other live section lost: '+name);
    }
    assert(!rendered.some(row=>row[0]==='decisions'),'unavailable historical log was rendered as valid/empty');
    assert.equal(rendered.find(row=>row[0]==='candidates')[1],1);
    assert(elements.updated.textContent.includes('更新于'));
    assert.equal(calls.length,8);
    assert(calls.every(c=>c.method==='GET'));

    failed.delete('/api/decisions');
    rendered.length=0;
    await ctx.refresh();
    assert(rendered.some(row=>row[0]==='decisions'&&row[1]===1));
    assert.equal(elements.decisions.innerHTML,'历史判断实际数量:1');
    assert(!elements.runtime.className.includes('offline'));

    failed.add('/api/runtime');
    await ctx.refresh();
    assert(elements.runtime.className.includes('offline'),'critical runtime error must still be visible');
    assert(elements.runtime.innerHTML.includes('/api/runtime 503'));
    failed.delete('/api/runtime');

    failed.add('/api/frank-observed-watchlist');
    await ctx.refresh();
    assert(!elements.runtime.className.includes('offline'),'existing watch fallback must stay available');
    failed.delete('/api/frank-observed-watchlist');

    console.log('FRANK_DECISIONS_503_ISOLATED_REAL_HTTP_REFRESH_PASS');
  } finally {
    await new Promise(resolve=>server.close(resolve));
  }
})().catch(err=>{console.error(err);process.exitCode=1});
