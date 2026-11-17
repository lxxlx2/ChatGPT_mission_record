import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const script=fs.readFileSync(new URL('../mission_agent/mission_control/static/frank_evidence_manifests.js',import.meta.url),'utf8');
const identity='a'.repeat(32);
const metadata={manifest_id:identity,state:'COMPLETE',counts:{frank_activity_rows:55}};
const page=(next=null)=>({manifest_id:identity,immutable_source_snapshot:true,rows:[{raw_trade_legs:[{body:'<img onerror=evil()>',amount:'18446744073709551615'}]}],total_signatures:55,returned:25,next_cursor:next});
const settle=async()=>{for(let n=0;n<15;n++)await new Promise(r=>setImmediate(r));};
function browser(backend){
  const elements=new Map(),calls=[];let sequence=0;
  const get=id=>{if(!elements.has(id))elements.set(id,{value:'',textContent:'',disabled:false,events:{},addEventListener(name,fn){this.events[name]=fn;},click(){if(!this.disabled)this.events.click?.();}});return elements.get(id);};
  const e=name=>get('frank-manifest-'+name);
  vm.runInNewContext(script,{document:{getElementById:get},fetch:async(path,opts)=>{calls.push({path,opts});return {ok:true,json:async()=>backend(path,opts)};},
    AbortController,crypto:{randomUUID:()=>String(++sequence)},setTimeout:()=>1,clearTimeout:()=>{},JSON,Number,String,encodeURIComponent});
  return {e,calls};
}
test('startup does not create or read; explicit capture records complete version without RPC',async()=>{
  const b=browser(()=>metadata);assert.equal(b.calls.length,0);
  b.e('create').click();await settle();
  assert.equal(b.calls.length,1);assert.equal(b.calls[0].path,'/api/frank-evidence-manifests');
  assert.deepEqual(JSON.parse(b.calls[0].opts.body),{kind:'activity',idempotency_key:'1'});
  assert.equal(b.e('id').value,identity);assert.match(b.e('status').textContent,/55/);
});
test('immutable activity pagination stays bound and raw facts render as text',async()=>{
  const b=browser(path=>page(path.includes('cursor=')?null:'more'));
  b.e('id').value=identity;b.e('read').click();await settle();
  assert.match(b.e('data').textContent,/<img onerror=evil\(\)>/);
  assert.equal(b.e('next').disabled,false);b.e('next').click();await settle();
  assert.ok(b.calls[1].path.includes('manifest_id='+identity)&&b.calls[1].path.includes('cursor=more'));
  assert.equal(b.e('next').disabled,true);
  assert.ok(b.calls.every(c=>!c.opts.method&&c.opts.headers['X-Frank-Research-Read']==='1'));
});
test('unconfirmed capture keeps identical idempotency key on retry',async()=>{
  let count=0;const b=browser(()=>{if(!count++)throw Error('SECRET_RPC_KEY');return metadata;});
  b.e('create').click();await settle();assert.match(b.e('status').textContent,/尚未确认/);
  b.e('create').click();await settle();assert.equal(b.calls[0].opts.body,b.calls[1].opts.body);
  assert.equal(b.e('status').textContent.includes('SECRET'),false);
});
test('fact capture validates the parent and sends it only on explicit fact creation',async()=>{
  const b=browser(()=>({...metadata,fact_revision_counts:{new:0,revised:3}}));
  b.e('parent').value='not-a-manifest';
  b.e('create-facts').click();await settle();
  assert.equal(b.calls.length,0);
  b.e('parent').value=identity;
  b.e('create-facts').click();await settle();
  assert.deepEqual(JSON.parse(b.calls[0].opts.body),{kind:'facts',idempotency_key:'1',supersedes_manifest_id:identity});
  assert.match(b.e('status').textContent,/修订 3 条/);
});
test('snapshot list pages all remain reachable',async()=>{
  const b=browser(path=>({rows:[metadata],total_matching:2,next_cursor:path.includes('cursor=')?null:'next'}));
  b.e('list').click();await settle();b.e('more').click();await settle();
  assert.equal((b.e('list-data').textContent.match(/manifest_id/g)||[]).length,2);
  assert.equal(b.e('more').disabled,true);
});
test('late snapshot response cannot replace a changed identity',async()=>{
  let resolve;const b=browser(()=>new Promise(r=>resolve=r));
  b.e('id').value=identity;b.e('read').click();await settle();
  b.e('id').value='b'.repeat(32);b.e('id').events.input();resolve(page());await settle();
  assert.equal(b.e('data').textContent,'');assert.equal(b.e('next').disabled,true);
});
