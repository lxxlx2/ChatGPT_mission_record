import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {test} from 'node:test';
import vm from 'node:vm';

const app=readFileSync(new URL('../mission_agent/mission_control/static/app.js',import.meta.url),'utf8');
const html=readFileSync(new URL('../mission_agent/mission_control/static/index.html',import.meta.url),'utf8');
const begin=app.indexOf('// D2: MANUAL/EXPLICIT local GET only.');
const end=app.indexOf("$('watch-filter').addEventListener",begin);
assert.ok(begin>=0 && end>begin,'isolate the real D2 page handlers, not a mocked replica');
const realSource=app.slice(begin,end);
const allControls=['frank-d2-panel','frank-d2-read','frank-d2-mint','frank-d2-find',
 'frank-d2-page-prev','frank-d2-page-next','frank-d2-summary','frank-d2-rows',
 'frank-d2-updated'];
for(const id of allControls)assert.ok(html.includes('id="'+id+'"'),'missing real HTML '+id);
const mint='So11111111111111111111111111111111111111112';
const doc={status:'BALANCE_AT_OBSERVED_FINALIZED_SLOTS_NOT_LIVE',
 observed_at_utc:'2026-10-23T14:46:32Z',observed_at_bangkok:'2026-10-23T21:46:32+07:00',
 age_seconds_at_response:3600,account_count:4148,mint_count:4148,
 program_coverage:[{program_id:'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA',slot:460482174},
                   {program_id:'TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb',slot:460482176}],
 page:0,total_pages:42,rows:[{mint,raw_amount:'12000000',decimals:6,
  account_count:2,slot_min:460482174,slot_max:460482174}],result_count:1};
function fixture(results=[]){
  const nodes=new Map(),calls=[];
  const get=id=>{
    if(!nodes.has(id))nodes.set(id,{value:'',textContent:'',innerHTML:'',disabled:false,
      listeners:{},addEventListener(event,cb){this.listeners[event]=cb;}});
    return nodes.get(id);
  };
  const ctx={ $:get, walletWatchData:{rows:[{mint,local_model_state:'CLOSED',last_event_side:'SELL'}]},
    esc:x=>String(x).replaceAll('<','&lt;'),short:x=>x.slice(0,8),
    copyButton:()=>'',encodeURIComponent,Number,String,
    fetch:async(path,opts)=>{
      calls.push({path,opts});
      if(opts.method!=='GET')throw Error('unexpected POST');
      const next=results.shift();
      if(!next)throw Error('unexpected request');
      const response=await next;
      return response instanceof Error?Promise.reject(response):{
        ok:true,status:200,json:async()=>response};
    }};
  vm.createContext(ctx);
  vm.runInContext(realSource,ctx);
  return {ctx,el:get,calls};
}
const task=body=>Promise.resolve(body);
function deferred(){let resolve;const promise=new Promise(r=>resolve=r);return {promise,resolve};}

test('D2 page does not automatically request private Mint source or send RPC',()=>{
  const h=fixture();
  assert.equal(h.calls.length,0);
  assert.equal(h.el('frank-d2-read').listeners.click instanceof Function,false);
  assert.ok(typeof h.el('frank-d2-read').listeners.click==='function');
});
test('explicit read uses same-origin GET and formats raw integer accurately',async()=>{
  const h=fixture([task(doc)]);
  await h.ctx.frankD2Read({page:0});
  assert.equal(h.calls.length,1);
  assert.equal(h.calls[0].path,'/api/frank-d2-at-slot?page=0');
  assert.equal(h.calls[0].opts.headers['X-Frank-D2-Read'],'1');
  assert.match(h.el('frank-d2-rows').innerHTML,/12 枚/);
  assert.match(h.el('frank-d2-rows').innerHTML,/CLOSED/);
  assert.match(h.el('frank-d2-summary').textContent,/非原子快照/);
  assert.equal(h.el('frank-d2-page-next').disabled,false);
});
test('exact Mint absent is never mapped to zero, without scan or POST',async()=>{
  const h=fixture([task({...doc,lookup_mint:mint,
    lookup_state:'NO_ACTIVE_OWNER_TOKEN_ACCOUNT_OBSERVED_AT_SLOTS',
    rows:[],result_count:0,total_pages:undefined})]);
  h.el('frank-d2-mint').value=mint;
  h.el('frank-d2-find').listeners.click();
  await new Promise(resolve=>setImmediate(resolve));
  assert.equal(h.calls.length,1);
  assert.equal(h.calls[0].path,'/api/frank-d2-at-slot?mint='+mint);
  assert.match(h.el('frank-d2-rows').innerHTML,/不是余额 0/);
  assert.equal(h.el('frank-d2-page-next').disabled,true);
});
test('missing imported file cannot display fabricated balances',async()=>{
  const h=fixture([task({status:'SOURCE_NOT_IMPORTED',rows:[]})]);
  await h.ctx.frankD2Read({page:0});
  assert.match(h.el('frank-d2-summary').textContent,/尚未经单独批准导入/);
  assert.match(h.el('frank-d2-rows').innerHTML,/不能按零仓位处理/);
});
test('late older request cannot overwrite a newer Mint or source failure state',async()=>{
  const older=deferred(),h=fixture([older.promise,task({status:'SOURCE_REJECTED',reason:'BAD_HASH'})]);
  const old=h.ctx.frankD2Read({page:0});
  await h.ctx.frankD2Read({mint});
  older.resolve(doc);
  await old;
  assert.match(h.el('frank-d2-summary').textContent,/BAD_HASH/);
  assert.doesNotMatch(h.el('frank-d2-rows').innerHTML,/12 枚/);
});
test('exact decimal formatting never uses JS floating point',()=>{
  const h=fixture();
  assert.equal(h.ctx.frankD2Decimal('1234567890123456789012345',9),
               '1234567890123456.789012345');
  assert.equal(h.ctx.frankD2Decimal('0',9),'0');
  assert.equal(h.ctx.frankD2Decimal('1000000000',9),'1');
});
