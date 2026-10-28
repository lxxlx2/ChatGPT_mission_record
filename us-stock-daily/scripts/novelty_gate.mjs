import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const HEADINGS=[
 '一、市场总览','二、正常时段、盘后与异动原因','三、行业级异动与结构性主题',
 '四、重大主题专题分析','五、AI、科技与一级市场','六、机构资金与市场观点',
 '七、政策、监管与全球局势','八、风险雷达','九、未来24至72小时事件日历',
 '十、今日买入观察','十一、漏检复盘与监控修正','十二、结论'
];
const routine=new Set(['ROUTINE_MARKET','ROUTINE_QUOTE','ROUTINE_ETF_DAY']);
const legitCalendar='CALENDAR';
export function validateStockNovelty(input){
 const errors=[],warnings=[];
 const fail=(name,detail)=>errors.push(name+':'+detail);
 const report=String(input.body||'');
 const headings=[],parsed=[];
 let section=0,num=0;
 for(const line of report.split(/\r?\n/)){
  if(/^[一二三四五六七八九十]+、/.test(line)){
   headings.push(line.trim());section++;num=0;continue;
  }
  const found=/^（(\d+)）(.*)$/.exec(line);
  if(found){num++;if(Number(found[1])!==num)fail('NUMBERING',section+'/'+found[1]);parsed.push({section,item_number:num,text:found[2]});}
 }
 if(headings.length!==12||headings.some((h,i)=>h!==HEADINGS[i]))fail('WRONG_12_HEADINGS',headings.length);
 const items=Array.isArray(input.items)?input.items:[];
 if(items.length!==parsed.length)fail('BODY_ITEMS_MISMATCH',items.length+'/'+parsed.length);
 const byKey=new Map();
 for(const ev of input.events||[]){
  if(!ev.event_key||byKey.has(ev.event_key))fail('DUPLICATE_OR_MISSING_EVENT',ev.event_key);
  byKey.set(ev.event_key,ev);
  if(!ev.family_key||!ev.material_version||!ev.kind||!/^https:\/\//.test(ev.source_url||'')||!ev.published_at)
    fail('MISSING_STABLE_PROVENANCE',ev.event_key);
 }
 // Mandatory independent original IPO and X-source discovery receipts in the
 // existing scheduled stock report. Browser access is conditional, not assumed.
 const ipoReceipts=Array.isArray(input.ipo_status_receipts)?input.ipo_status_receipts:[];
 if(!ipoReceipts.length)fail('IPO_STATUS_SWEEP_MISSING','no_issuer_pipeline_receipt');
 for(const a of ipoReceipts){
  if(!a.issuer_name||!/^https:\/\//.test(a.official_url||'')||!a.checked_at||!a.stage||!['MATERIAL_DELTA','NO_DELTA','SOURCE_GAP'].includes(a.new_delta_or_none))
    fail('INVALID_IPO_SOURCE_RECEIPT',String(a.issuer_name||'unknown'));
  if(a.new_delta_or_none==='SOURCE_GAP'&&!a.error)fail('IPO_SOURCE_GAP_WITHOUT_REASON',a.issuer_name);
 }
 const xr=input.x_source_receipt||null;
 if(!xr||!xr.checked_at||!['AVAILABLE','UNAVAILABLE'].includes(xr.browser_session)||
      !['ORIGINAL_READ','PUBLIC_ORIGINAL_LOOKUP','SOURCE_GAP'].includes(xr.status)||
      (xr.status==='ORIGINAL_READ'&& (xr.browser_session!=='AVAILABLE'||!/^https:\/\/(x\.com|twitter\.com)\//.test(xr.original_post_url||'')))||
      (xr.status==='PUBLIC_ORIGINAL_LOOKUP'&&!/^https:\/\//.test(xr.fallback_url||''))||
      (xr.status==='SOURCE_GAP'&&!xr.error))
   fail('X_SOURCE_PROVENANCE_MISSING','scheduled_runtime_source_receipt');
 const count=new Map(),history=Array.isArray(input.previous_events)?input.previous_events:[];
 for(let i=0;i<parsed.length;i++){
  const item=items[i],line=parsed[i];
  if(!item||item.section!==line.section||item.item_number!==line.item_number||item.text!==line.text)fail('ITEM_BODY_MISMATCH',i);
  if(!item)continue;
  if(!byKey.has(item.event_key)){fail('ITEM_WITHOUT_EVENT',item.event_key);continue;}
  count.set(item.event_key,(count.get(item.event_key)||0)+1);
  const event=byKey.get(item.event_key);
  if(item.section!==event.primary_section)fail('WRONG_PRIMARY_HOME',event.event_key+'/'+item.section);
  if(event.kind===legitCalendar && item.section!==9)fail('CALENDAR_REPEATED_OUTSIDE_CALENDAR',event.event_key);
  if(event.kind==='IPO_ISSUER_STAGE'&&(item.section!==5||!/IPO|Pre-IPO|新股/i.test(String(item.text||''))))fail('IPO_STAGE_NOT_IN_IPO_SECTION',event.event_key);
 }
 for(const [key,n] of count){
  if(n>1)fail('DUPLICATE_SAME_DAY_STORY',key+'/'+n);
 }
 for(const ev of input.events||[]){
  if(!count.has(ev.event_key))continue;
  const prev=history.filter(x=>x.family_key===ev.family_key);
  if(!prev.length)continue;
  if(routine.has(ev.kind)){
   if(!ev.observation_date||prev.some(x=>x.observation_date===ev.observation_date))
     fail('REPLAYED_MARKET_SESSION',ev.family_key);
   continue;
  }
  if(ev.kind===legitCalendar){
   const upcoming=/^\d{4}-\d{2}-\d{2}/.test(ev.calendar_date||'');
   if(!upcoming||count.get(ev.event_key)!==1)fail('CALENDAR_NO_VERIFIED_DATE',ev.event_key);
   continue;
  }
  if(prev.some(x=>x.material_version===ev.material_version)){fail('REPEATED_FAMILY_VERSION',ev.family_key);continue;}
  const proof=ev.novelty_proof;
  const valid=proof&&prev.some(x=>x.material_version===proof.previous_material_version)
    && String(proof.changed_field||'').length>=4
    && String(proof.old_value||'').trim().length>=3
    && String(proof.new_value||'').trim().length>=3
    && String(proof.old_value).trim().toLowerCase()!==String(proof.new_value).trim().toLowerCase()
    && /^https:\/\//.test(proof.evidence_url||'')
    && String(proof.evidence_published_at||'').length>=10
    && items.some(x=>x.event_key===ev.event_key&&String(x.text||'').toLowerCase().includes(String(proof.new_value).trim().toLowerCase()));
  if(!valid)fail('NO_NEW_FACT_FOR_OLD_STORY',ev.family_key);
 }
 if(!Array.isArray(input.previous_days_checked)||input.previous_days_checked.length<7)
   warnings.push('PREVIOUS_SEVEN_SENT_DAYS_NOT_PROVEN');
 return {passed:errors.length===0,errors,warnings,
  metrics:{sections:headings.length,numbered_items:parsed.length,event_families:byKey.size,prior_observations:history.length}};
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 if(process.argv.length!==3){process.stderr.write('Usage: node novelty_gate.mjs manifest.json\n');process.exitCode=2;}
 else{const v=validateStockNovelty(JSON.parse(fs.readFileSync(process.argv[2],'utf8')));process.stdout.write(JSON.stringify(v,null,2)+'\n');process.exitCode=v.passed?0:1;}
}
