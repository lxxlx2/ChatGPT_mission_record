import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const script = fs.readFileSync(new URL('../mission_agent/mission_control/static/frank_watch_metadata.js', import.meta.url), 'utf8');
const mint = '11111111111111111111111111111112';
const other = '11111111111111111111111111111113';
const row = (m=mint, revision=0, values={}) => ({mint:m,revision,pinned:false,note:'',watch_override:'DEFAULT',person_id:'frank',chain:'solana',...values});
const settle = async () => {for(let n=0;n<12;n++) await new Promise(r=>setImmediate(r));};
function browser(fetcher) {
  class Element {
    constructor(tag='div'){this.tag=tag;this.value='';this.checked=false;this.disabled=false;this.textContent='';this.children=[];this.events={};}
    addEventListener(name,fn){(this.events[name]??=[]).push(fn);}
    dispatch(name){for(const fn of this.events[name]||[])fn();}
    click(){if(!this.disabled)this.dispatch('click');}
    appendChild(node){node.parent=this;this.children.push(node);return node;}
    replaceChildren(){this.children=[];}
    remove(){this.parent.children=this.parent.children.filter(n=>n!==this);}
    set innerHTML(_){throw Error('UNSAFE_HTML_ASSIGNMENT');}
  }
  const elements=new Map();
  const get=id=>{if(!elements.has(id))elements.set(id,new Element());return elements.get(id);};
  const e=name=>get('frank-watch-meta-'+name);
  e('override').value='DEFAULT';
  const calls=[], timers=new Map();let sequence=0;
  vm.runInNewContext(script,{
    document:{getElementById:get,createElement:tag=>new Element(tag)},
    fetch:async(path,opts)=>{calls.push({path,opts});const value=await fetcher(path,opts);return {ok:!(value?.status>=400),status:value?.status||200,json:async()=>value?.body??value};},
    crypto:{randomUUID:()=> 'request-'+(++sequence)},AbortController,
    setTimeout:fn=>{const id=++sequence;timers.set(id,fn);return id;},clearTimeout:id=>timers.delete(id),
    Date,Map,Set,JSON,String,Number,Math,encodeURIComponent,
  });
  const input=(name,value)=>{e(name).value=value;e(name).dispatch('input');};
  return {e,calls,input,timers};
}
const emptyEvents={rows:[],next_cursor:null};
const data=(r=row())=>({rows:[r],total_matching:1,next_cursor:null});

test('startup and mint change never write or fetch automatically',()=>{
  const b=browser(()=>{throw Error('unexpected');});
  assert.equal(b.calls.length,0);
  b.input('mint',mint);
  assert.equal(b.e('save').disabled,true);
  assert.equal(b.calls.length,0);
});
test('explicit load-save-page reload keeps backend note and revision',async()=>{
  let saved=row();
  const backend=(path,opts)=>path.includes('-events')?emptyEvents:opts.method==='PATCH'?
    (saved={...saved,...JSON.parse(opts.body),revision:saved.revision+1}):data(saved);
  const first=browser(backend);first.input('mint',mint);first.e('load').click();await settle();
  first.input('note','multi\nline');first.e('pinned').checked=true;first.e('save').click();await settle();
  assert.equal(saved.revision,1);
  const second=browser(backend);assert.equal(second.calls.length,0);
  second.input('mint',mint);second.e('load').click();await settle();
  assert.equal(second.e('note').value,'multi\nline');assert.equal(second.e('pinned').checked,true);
  assert.match(second.e('status').textContent,/版本 1/);
  assert.equal(second.calls.some(c=>c.opts.method==='PATCH'),false);
});
test('409 preserves draft and blocks saving until explicit latest read',async()=>{
  let latest=0, conflicts=true;
  const b=browser((path,opts)=>path.includes('-events')?emptyEvents:opts.method==='PATCH'?
    conflicts?{status:409,body:{error:'REVISION_CONFLICT'}}:row(mint,2,JSON.parse(opts.body)):data(row(mint,latest)));
  b.input('mint',mint);b.e('load').click();await settle();b.input('note','my draft');
  b.e('save').click();await settle();assert.equal(b.e('save').disabled,true);
  assert.equal(b.e('note').value,'my draft');assert.match(b.e('status').textContent,/版本冲突/);
  latest=1;conflicts=false;b.e('load').click();await settle();
  assert.equal(b.e('note').value,'my draft');assert.equal(b.e('save').disabled,false);
  b.e('save').click();await settle();
  const patches=b.calls.filter(c=>c.opts.method==='PATCH');
  assert.equal(JSON.parse(patches[1].opts.body).expected_revision,1);
  assert.notEqual(JSON.parse(patches[0].opts.body).idempotency_key,JSON.parse(patches[1].opts.body).idempotency_key);
});
test('unconfirmed timeout retry uses identical request key and body',async()=>{
  let attempts=0;
  const b=browser((path,opts)=>{
    if(path.includes('-events'))return emptyEvents;
    if(opts.method==='PATCH'){if(!attempts++)throw Error('private transport failure');return row(mint,1,JSON.parse(opts.body));}
    return data();
  });
  b.input('mint',mint);b.e('load').click();await settle();b.input('note','retry');
  b.e('save').click();await settle();assert.match(b.e('status').textContent,/尚未确认/);
  b.e('save').click();await settle();
  const patches=b.calls.filter(c=>c.opts.method==='PATCH');
  assert.equal(patches[0].opts.body,patches[1].opts.body);
  assert.equal(b.e('status').textContent.includes('private'),false);
  assert.equal(b.timers.size,0);
});
test('request deadline abort preserves draft and allows the same retry',async()=>{
  let hang=true;
  const b=browser((path,opts)=>{
    if(path.includes('-events'))return emptyEvents;
    if(opts.method==='PATCH'&&hang)return new Promise((resolve,reject)=>opts.signal.addEventListener('abort',()=>reject(Error('timeout'))));
    return opts.method==='PATCH'?row(mint,1,JSON.parse(opts.body)):data();
  });
  b.input('mint',mint);b.e('load').click();await settle();b.input('note','keep');b.e('save').click();await settle();
  assert.equal(b.e('save').disabled,true);
  for(const timer of [...b.timers.values()])timer();await settle();
  assert.equal(b.e('save').disabled,false);assert.equal(b.e('note').value,'keep');
  hang=false;b.e('save').click();await settle();
  const patches=b.calls.filter(c=>c.opts.method==='PATCH');assert.equal(patches[0].opts.body,patches[1].opts.body);
});
test('late response for previous Mint cannot authorize saving another Mint',async()=>{
  let release;
  const b=browser(path=>path.includes(mint)?new Promise(r=>release=r):data(row(other)));
  b.input('mint',mint);b.e('load').click();await settle();b.input('mint',other);
  release(data());await settle();assert.equal(b.e('save').disabled,true);
  assert.equal(b.e('note').value,'');
});
test('empty or wrong-identity response never invents a default revision',async()=>{
  for(const payload of [{rows:[]},data(row(other)),data({...row(),revision:true})]){
    const b=browser(()=>payload);b.input('mint',mint);b.e('load').click();await settle();
    assert.equal(b.e('save').disabled,true);
  }
});
test('all saved records and next pages are reachable; list mode cannot save a row accidentally',async()=>{
  const b=browser(path=>path.includes('cursor=')?{rows:[row(other,1)],next_cursor:null,total_matching:2}:
    {rows:[row(mint,1)],next_cursor:'page-2',total_matching:2});
  b.e('load').click();await settle();assert.equal(b.e('save').disabled,true);
  b.e('next').click();await settle();assert.equal(b.e('rows').children.length,2);
  assert.equal(b.e('next').disabled,true);assert.equal(b.calls.some(c=>c.opts.method==='PATCH'),false);
});
test('notes and audit changes render as inert text; source and sender APIs are never called',async()=>{
  const note='<img src=x onerror=alert(1)>\n<script>attack()</script>';
  const b=browser(path=>path.includes('-events')?{rows:[{mint,revision:1,event_id:'event',created_at:100,before:{note:''},after:{note}}]}:
    data(row(mint,1,{note})));
  b.e('load').click();await settle();
  assert.equal(b.e('rows').children[0].children[2].textContent,note);
  b.input('mint',mint);b.e('load').click();await settle();assert.equal(b.e('note').value,note);
  assert.match(b.e('history').children[0].textContent,/<script>/);
  assert.ok(b.calls.every(c=>c.path.startsWith('/api/frank-watch-metadata')));
});

test('watch selection and pin sorting affect the user view while all and hidden remain reachable',()=>{
  const app=fs.readFileSync(new URL('../mission_agent/mission_control/static/app.js',import.meta.url),'utf8');
  const start=app.indexOf('const watchLabels =');
  const end=app.indexOf('// D1:',start);
  const elements=new Map();
  const get=id=>{if(!elements.has(id))elements.set(id,{value:'',textContent:'',innerHTML:''});return elements.get(id);};
  get('watch-filter').value='WATCH_NOW';
  const context=vm.createContext({$:get,esc:s=>String(s),short:s=>s,copyButton:()=>'',Date,Number,String,
    encodeURIComponent,translated:()=>'',sideLabel:{}});
  vm.runInContext(app.slice(start,end),context);
  context.payload={status:'OK',summary:{total_observed:2},rows:[
    {mint:'hidden',watch_state:'MODEL_OPEN',user_metadata:{watch_override:'HIDE'}},
    {mint:'ordinary',watch_state:'MODEL_OPEN'},
    {mint:'followed',watch_state:'USER_ONLY',user_metadata:{watch_override:'FOLLOW',pinned:true}},
  ]};
  vm.runInContext('renderFrankWatchlist(payload)',context);
  assert.doesNotMatch(get('watch-rows').innerHTML,/hidden/);
  assert.ok(get('watch-rows').innerHTML.indexOf('followed')<get('watch-rows').innerHTML.indexOf('ordinary'));
  assert.match(get('watch-rows').innerHTML,/尚无本地买卖记录/);
  get('watch-filter').value='ALL';vm.runInContext('renderFrankWatchlist(payload)',context);
  assert.match(get('watch-rows').innerHTML,/hidden/);
  get('watch-filter').value='USER_HIDDEN';vm.runInContext('renderFrankWatchlist(payload)',context);
  assert.match(get('watch-rows').innerHTML,/hidden/);assert.doesNotMatch(get('watch-rows').innerHTML,/ordinary|followed/);
  assert.equal(context.payload.rows[0].watch_state,'MODEL_OPEN');
});
