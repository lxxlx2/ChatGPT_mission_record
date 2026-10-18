'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'../mission_agent/mission_control/static/app.js'),'utf8');
const html=fs.readFileSync(path.join(__dirname,'../mission_agent/mission_control/static/index.html'),'utf8');
const start='async function loadArchivedClusterReadOnly() {';
const end='function setView(name) {';
const from=source.indexOf(start),to=source.indexOf(end,from+start.length);
assert(from>=0&&to>from);
assert(html.includes('id="cluster-archive-load"'));
assert(html.includes('查看已有归档（只读）'));
assert(source.includes("$('cluster-archive-load').addEventListener('click', loadArchivedClusterReadOnly)"));
const mint='EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v';
const elements={
 'cluster-mint':{value:mint},
 'cluster-archive-load':{disabled:false}
};
const statuses=[],rendered=[],requests=[];
const response={
 mint,
 observed_at:1720000000,
 execution_quote_30_usdc:{status:'OK',route_exists:true,execution_price_usdc:'1.23',
  price_impact_pct:'0.1',freshness_status:'CURRENT_AT_RESPONSE',is_current_at_response:true},
 metrics:{RAW_TOP10_PCT:'14'}
};
let returned=response;
const fn=new Function('$','get','renderClusterReport','clusterStatus',source.slice(from,to)+
 ';return loadArchivedClusterReadOnly')(
 id=>elements[id],
 async uri=>{requests.push(uri);if(returned instanceof Error)throw returned;return returned;},
 r=>rendered.push(r),
 (...args)=>statuses.push(args)
);
(async()=>{
 await fn();
 assert.equal(elements['cluster-archive-load'].disabled,false);
 assert.deepEqual(requests,['/api/cluster-latest?mint='+encodeURIComponent(mint)]);
 assert.equal(rendered.length,1);
 assert.equal(rendered[0].mint,mint);
 assert.equal(rendered[0].execution_quote_30_usdc.is_current_at_response,false);
 assert.equal(rendered[0].execution_quote_30_usdc.freshness_status,'ARCHIVED_NOT_LIVE');
 assert.equal(response.execution_quote_30_usdc.is_current_at_response,true,'upstream unmodified');
 assert.match(statuses.at(-1)[1],/历史/);
 assert.match(statuses.at(-1)[2],/不是当前链上扫描/);
 elements['cluster-mint'].value='invalid not-a-CA';
 await fn();
 assert.equal(requests.length,1,'invalid CA must not call endpoint');
 assert.match(statuses.at(-1)[1],/有效/);
 elements['cluster-mint'].value=mint;
 returned={...response,mint:'So11111111111111111111111111111111111111112'};
 await fn();
 assert.equal(rendered.length,1,'different mint never rendered');
 assert.match(statuses.at(-1)[1],/没有可读取/);
 returned=new Error('NOT_FOUND');
 await fn();
 assert.equal(rendered.length,1);
 assert.equal(elements['cluster-archive-load'].disabled,false);
 assert(requests.every(x=>x.startsWith('/api/cluster-latest?mint=')));
 assert(!source.slice(from,to).includes('/api/cluster-analysis'));
 console.log('FRANK_C02_EXACT_CA_ARCHIVED_GET_ONLY_PASS');
})().catch(e=>{console.error(e);process.exitCode=1});
