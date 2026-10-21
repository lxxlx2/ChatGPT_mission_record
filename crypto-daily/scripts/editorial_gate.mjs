import fs from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

export function validateEditorial(input, rules) {
  const errors=[],warnings=[],details={};
  const fail=(code,info)=>errors.push(code+':'+info);
  const report=String(input.body||'');
  const headings=[];
  const parsed=[];
  let section=0,number=0;
  for(const line of report.split(/\r?\n/)){
    if(/^[一二三四五六七八九十]+、/.test(line)){
      headings.push(line.trim());section++;number=0;
    }else{
      const m=/^（(\d+)）(.*)$/.exec(line);
      if(m){number++;if(Number(m[1])!==number)fail('NUMBERING',section+'/'+m[1]);parsed.push({section,item_number:number,text:m[2]});}
    }
  }

  const expected=[
    '一、今日最重要的5件事','二、BTC/ETH/SOL及主要资产','三、二级市场剧烈波动与持续趋势',
    '四、监管与政策','五、机构、VC、基金、交易所、上市公司、做市商、鲸鱼真实资金动作',
    '六、融资、协议、基础设施、稳定币、RWA、预测市场、AI/Crypto、DePIN及公链生态',
    '七、空投、积分、TGE、ICO/公售、解锁和实际可参与机会','八、Early / Meme / NFT / 新生态热点',
    '九、安全、黑客、漏洞、恶意App、脱锚、跑路、清算与重大解锁',
    '十、全球局势与跨市场冲击','十一、未来24至72小时催化',
    '十二、持续趋势与跨市场机会观察清单','十三、今日行动与风险结论'
  ];
  if(headings.length!==13||headings.some((h,i)=>h!==expected[i]))fail('FULL_13_CHAPTERS','wrong_heading_order_or_count');
  if(parsed.length===0)fail('EMPTY_REPORT','no_items');
  const declared=Array.isArray(input.items)?input.items:[];
  if(declared.length!==parsed.length)fail('ITEM_MANIFEST_NOT_COMPLETE',declared.length+'/'+parsed.length);
  for(let i=0;i<parsed.length;i++){
    const x=parsed[i],d=declared[i];
    if(!d||d.section!==x.section||d.item_number!==x.item_number||d.text!==x.text)fail('ITEM_MANIFEST_BODY_MISMATCH',i);
  }
  const lanes=rules.full_report.minimum_domain_receipts;
  const receipts=Array.isArray(input.source_receipts)?input.source_receipts:[];
  for(const lane of lanes){
    const found=receipts.filter(r=>r.lane===lane);
    if(found.length!==1)fail('DISCOVERY_LANE_RECEIPT_MISSING',lane);
    else {
      const receipt=found[0];
      if(!['checked','source_gap'].includes(receipt.status)||!receipt.checked_at||!receipt.query_or_url)fail('UNTRUSTED_SOURCE_RECEIPT',lane);
      if(receipt.status==='source_gap'){
        if(!receipt.error)fail('SOURCE_GAP_NO_REASON',lane);
        else warnings.push('SOURCE_GAP:'+lane);
      }else if(!receipt.result_urls?.length)fail('CHECKED_WITHOUT_SOURCE_RESULT',lane);
    }
  }
  const markets=Array.isArray(input.market_core)?input.market_core:[];
  for(const symbol of rules.full_report.market_core_must_have){
    const matches=markets.filter(x=>x.symbol===symbol && Number.isFinite(Number(x.price))&&Number(x.price)>0&&x.observed_at&&x.source_url);
    if(matches.length!==1)fail('MARKET_CORE_MISSING',symbol);
  }
  const byId=new Map();
  for(const ev of input.events||[]){
    if(!ev.event_key||byId.has(ev.event_key))fail('INVALID_OR_DUPLICATE_EVENT_KEY',ev.event_key||'nil');
    byId.set(ev.event_key,ev);
    if(!ev.material_version||!ev.kind||!ev.source_url||!ev.published_at||!ev.actual_delta)fail('EVENT_PROVENANCE_MISSING',ev.event_key);
    if(!rules.routing.some(r=>r.kind===ev.kind))fail('UNKNOWN_EVENT_KIND',ev.event_key);
  }
  const historical=new Set((input.previous_events||[]).map(e=>e.event_key+'::'+e.material_version));
  const counts=new Map(),highlights=[];
  for(const item of declared){
    const ev=byId.get(item.event_key);
    if(!ev){fail('ITEM_WITHOUT_EVENT',item.event_key||'nil');continue}
    counts.set(ev.event_key,(counts.get(ev.event_key)||0)+1);
    if(historical.has(ev.event_key+'::'+ev.material_version))fail('REPEATED_HISTORICAL_EVENT',ev.event_key);
    if(item.section===1){
      highlights.push(item);
      if(item.role!=='highlight')fail('TOP5_ROLE_INVALID',ev.event_key);
      if(!rules.top_highlights.allow_kinds.includes(ev.kind)||
         !rules.top_highlights.impact_required.includes(ev.impact)||
         ev.user_only===true||ev.no_material_delta===true||ev.source_confirmed===false||
         !['market-wide','multi-venue','sector-wide'].includes(ev.impact_breadth)||
         String(ev.top5_basis||'').length<40||
         !/^https:\/\//.test(ev.top5_evidence_url||''))fail('TOP5_NOT_ELIGIBLE',ev.event_key+'/'+ev.kind);
    }else{
      if(item.role!=='detail')fail('DETAIL_ROLE_INVALID',ev.event_key);
      const expectedRoute=rules.routing.find(r=>r.kind===ev.kind);
      if(expectedRoute&&expectedRoute.section!==item.section)fail('WRONG_PRIMARY_SECTION',ev.event_key+':'+item.section+' expected '+expectedRoute.section);
    }
  }
  if(highlights.length>5)fail('TOP5_OVER_CAPACITY',highlights.length);
  for(const [key,count] of counts.entries()){
    if(count>2)fail('OVEREXPOSED_EVENT',key+':'+count);
    const ones=declared.filter(x=>x.event_key===key);
    if(ones.length===2 && !(ones.some(x=>x.section===1)&&ones.some(x=>x.section!==1)))fail('REPEATED_EVENT_WITHOUT_HIGHLIGHT_DETAIL',key);
  }
  for(const ev of input.events||[]){
    if(ev.priority==='HIGH'&&ev.status==='verified'&&!counts.has(ev.event_key) && !ev.excluded_reason)fail('UNACCOUNTED_HIGH_EVENT',ev.event_key);
    if(ev.no_material_delta===true && counts.has(ev.event_key))fail('OLD_EVENT_REPLAY',ev.event_key);
  }
  let blank=0;
  for(let n=2;n<=13;n++){
    const present=parsed.filter(x=>x.section===n).length;
    if(!present){
      blank++;
      if(!report.includes(expected[n-1]+'\n'+rules.full_report.empty_section_line))fail('SECTION_WITHOUT_CONTENT_OR_NO_NEW',n);
      const reason=(input.empty_section_reasons||[]).find(x=>x.section===n);
      if(!reason||String(reason.reason||'').length<25||!Array.isArray(reason.checked_lanes)||!reason.checked_lanes.length)fail('BLANK_SECTION_WITHOUT_REVIEW',n);
      else if(reason.checked_lanes.some(lane=>!receipts.some(r=>r.lane===lane)))fail('BLANK_SECTION_SOURCE_NOT_CHECKED',n);
    }
  }
  if(!parsed.some(x=>x.section===2))fail('MARKET_REPORT_MISSING_CORE_CONTENT',2);
  const coreTexts=parsed.filter(x=>x.section===2).map(x=>x.text);
  for(const symbol of rules.full_report.market_core_must_have){
    const containsActualNumber=coreTexts.some(s=>new RegExp(symbol+'(?:\\/USDT)?[^\\n]{0,100}[0-9][0-9,.]*','i').test(s));
    if(!containsActualNumber)fail('CORE_PRICE_NOT_REPORTED_IN_BODY',symbol);
  }
  if(!parsed.some(x=>x.section===13))fail('REPORT_MISSING_DECISION_CONCLUSION',13);
  if(receipts.filter(r=>r.status==='checked'&&r.result_urls?.length).length<2)fail('INSUFFICIENT_VERIFIED_SOURCE_COVERAGE',receipts.length);
  details.blank_sections=blank;
  details.headings=headings.length;details.numbered_items=parsed.length;details.highlight_count=highlights.length;
  details.source_lanes=receipts.length;details.event_count=byId.size;
  return {passed:errors.length===0,errors,warnings,metrics:details};
}

if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
  if(process.argv.length!==4){process.stderr.write('Usage: node crypto-daily/scripts/editorial_gate.mjs manifest.json EDITORIAL_RULESET.json\n');process.exitCode=2;}
  else{
    const manifest=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
    const rules=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));
    const result=validateEditorial(manifest,rules);
    process.stdout.write(JSON.stringify(result,null,2)+'\n');
    process.exitCode=result.passed?0:1;
  }
}
