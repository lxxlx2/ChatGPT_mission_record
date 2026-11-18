/* Explicit local-index captures, immutable paging and plain-text evidence. */
(() => {
  'use strict';
  const el = name => document.getElementById('frank-manifest-'+name);
  if (!el('create')) return;
  let epoch=0, busy=false, next=null, selected=null, pendingCreate=null, listNext=null;
  const id=()=>el('id').value.trim();
  function controls(){
    for(const name of ['create','create-facts','parent','list','read']){
      const control=el(name);
      if(control)control.disabled=busy;
    }
    el('next').disabled=busy||!next||selected!==id();
    el('more').disabled=busy||!listNext;
  }
  async function request(path,body){
    const controller=new AbortController();
    // A full local archive replay completes at the pace of the source dataset.
    const timer=body?.kind==='facts'?null:setTimeout(()=>controller.abort(),30000);
    try{
      const response=await fetch(path,{cache:'no-store',signal:controller.signal,...(body===undefined?
        {headers:{'X-Frank-Research-Read':'1'}}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})});
      const value=await response.json();
      if(!response.ok)throw Error('LOCAL_MANIFEST_REQUEST_FAILED');
      return value;
    }finally{if(timer!==null)clearTimeout(timer);}
  }
  function archiveSummary(summary){
    if(!summary)return '';
    const keys=['verified','missing','mismatched','other_unresolved','reclassified',
      'executed_token_transfers','executed_native_transfers','attempted_transfers','confirmed_initial_fundings'];
    if(!keys.every(key=>Number.isSafeInteger(summary[key])&&summary[key]>=0)){
      return ' 原文复核统计暂不可用。';
    }
    return ' 整份快照原文复核：已核实 '+summary.verified+' 笔，归档缺失 '+summary.missing+
      ' 笔，摘要或交易身份不符 '+summary.mismatched+' 笔，其他未核实 '+summary.other_unresolved+
      ' 笔。已核实交易中，'+summary.reclassified+' 笔的重放分类与原索引不同。'+
      ' 已执行的代币转账指令 '+summary.executed_token_transfers+' 条、涉及钱包的 SOL 转账指令 '+
      summary.executed_native_transfers+' 条；失败交易中的转账尝试 '+summary.attempted_transfers+
      ' 条。核实关联代币账户初始注资 '+summary.confirmed_initial_fundings+' 条。';
  }
  async function list(cursor=null){
    if(busy)return;busy=true;const token=++epoch;controls();
    try{
      const result=await request('/api/frank-evidence-manifests?limit=100'+(cursor?'&cursor='+encodeURIComponent(cursor):''));
      if(token!==epoch)return;
      if(!Array.isArray(result.rows))throw Error('INVALID_LIST');
      const text=JSON.stringify(result.rows,null,2);
      el('list-data').textContent=(cursor?el('list-data').textContent+'\n':'')+text;
      listNext=result.next_cursor||null;
      el('status').textContent='已读取固定快照列表，共 '+result.total_matching+' 份；选择 manifest_id 后读取。';
    }catch(_){if(token===epoch)el('status').textContent='固定快照列表暂不可读，请重新读取第一页。';}
    finally{busy=false;controls();}
  }
  async function read(cursor=null){
    if(busy)return;const identity=id();
    if(!/^[a-f0-9]{32}$/.test(identity)){el('status').textContent='请输入完整 manifest_id。';return;}
    busy=true;const token=++epoch;controls();
    try{
      const result=await request('/api/frank-evidence-activity?manifest_id='+identity+'&limit=25'+(cursor?'&cursor='+encodeURIComponent(cursor):''));
      if(token!==epoch||identity!==id())return;
      if(result.manifest_id!==identity||result.immutable_source_snapshot!==true||!Array.isArray(result.rows))throw Error('INVALID_MANIFEST');
      selected=identity;next=result.next_cursor||null;
      el('data').textContent=JSON.stringify(result,null,2);
      el('status').textContent='固定本地历史：共 '+result.total_signatures+' 条，本页 '+result.returned+' 条'+(next?'；可继续下一页。':'；已到末页。')+' 完整链史未核实。'+archiveSummary(result.archive_replay_summary);
    }catch(_){if(token===epoch){next=null;el('status').textContent='固定快照读取失败；未改读当前索引，旧快照和页面内容保留。';}}
    finally{busy=false;controls();}
  }
  async function create(kind){
    if(busy)return;
    const parent=kind==='facts'?(el('parent')?.value||'').trim():'';
    if(parent&&!/^[a-f0-9]{32}$/.test(parent)){
      el('status').textContent='请输入完整的来源快照 ID。';
      return;
    }
    if(!pendingCreate||pendingCreate.kind!==kind||pendingCreate.parent!==parent){
      pendingCreate={kind,parent,key:crypto.randomUUID()};
    }
    busy=true;
    const token=++epoch;
    controls();
    el('status').textContent=kind==='facts'?'正在固定钱包事实并逐笔核对本地归档，请等待完成。':'正在固定本地索引。';
    try{
      const payload={kind,idempotency_key:pendingCreate.key};
      if(parent)payload.supersedes_manifest_id=parent;
      const result=await request('/api/frank-evidence-manifests',payload);
      if(token!==epoch)return;
      if(result.state!=='COMPLETE'||!/^[a-f0-9]{32}$/.test(result.manifest_id))throw Error('INCOMPLETE');
      el('id').value=result.manifest_id;selected=null;next=null;pendingCreate=null;
      el('data').textContent=JSON.stringify(result,null,2);
      const counts=result.fact_revision_counts;
      el('status').textContent='已固定 '+result.counts.frank_activity_rows+' 条本地活动'+
        (counts?'，新增 '+counts.new+' 条交易事实，修订 '+counts.revised+' 条。':'及全部源表。')+
        archiveSummary(result.archive_replay_summary)+' 点击读取固定历史分页。';
    }catch(_){if(token===epoch)el('status').textContent='固定结果尚未确认；可重试同一创建请求，或读取快照列表核对。';}
    finally{busy=false;controls();}
  }
  el('id').addEventListener('input',()=>{++epoch;selected=null;next=null;controls();});
  el('create').addEventListener('click',()=>{void create('activity');});
  el('create-facts')?.addEventListener('click',()=>{void create('facts');});
  el('list').addEventListener('click',()=>{void list();});
  el('more').addEventListener('click',()=>{if(listNext)void list(listNext);});
  el('read').addEventListener('click',()=>{void read();});
  el('next').addEventListener('click',()=>{if(next&&selected===id())void read(next);});
  controls();
})();
