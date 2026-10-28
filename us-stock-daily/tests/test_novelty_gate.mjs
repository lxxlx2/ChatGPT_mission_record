import test from 'node:test';
import assert from 'node:assert/strict';
import {validateStockNovelty} from '../scripts/novelty_gate.mjs';
const headings=['一、市场总览','二、正常时段、盘后与异动原因','三、行业级异动与结构性主题','四、重大主题专题分析','五、AI、科技与一级市场','六、机构资金与市场观点','七、政策、监管与全球局势','八、风险雷达','九、未来24至72小时事件日历','十、今日买入观察','十一、漏检复盘与监控修正','十二、结论'];
function make(){
 const items=headings.map((_,i)=>({section:i+1,item_number:1,event_key:'news-'+(i+1),text:'有日期和真实源的新事实-'+(i+1)}));
 const events=items.map(t=>({event_key:t.event_key,family_key:'stable-family-'+t.event_key,material_version:'original-2026-10-28',primary_section:t.section,kind:t.section===1?'ROUTINE_MARKET':t.section===9?'CALENDAR':'NEW_MATERIAL',observation_date:'2026-10-27',calendar_date:'2026-10-29',source_url:'https://example.org/issuer',published_at:'2026-10-28T01:20:00Z'}));
 return {body:headings.map((h,i)=>h+'\n（1）'+items[i].text).join('\n\n'),items,events,previous_events:[],previous_days_checked:['2026-10-21','2026-10-22','2026-10-23','2026-10-24','2026-10-25','2026-10-26','2026-10-27'],ipo_status_receipts:[{issuer_name:'Anthropic',official_url:'https://www.sec.gov/edgar/browse/',checked_at:'2026-10-28T02:00:00Z',stage:'PUBLIC_S1',new_delta_or_none:'NO_DELTA'}],x_source_receipt:{checked_at:'2026-10-28T02:00:00Z',browser_session:'UNAVAILABLE',status:'PUBLIC_ORIGINAL_LOOKUP',fallback_url:'https://x.com/AnthropicAI'}};
}
test('complete 12-section new-date facts pass',()=>assert.equal(validateStockNovelty(make()).passed,true));
test('same family new date key cannot repeat identical issuer version',()=>{
 const v=make();v.previous_events=[{event_key:'other-yesterday',family_key:'stable-family-news-5',material_version:'original-2026-10-28'}];
 assert.ok(validateStockNovelty(v).errors.some(e=>e.startsWith('REPEATED_FAMILY_VERSION')));
});
test('the Fed is about to decide cannot count as new release by changing title',()=>{
 const v=make();v.previous_events=[{event_key:'old-timer',family_key:'stable-family-news-7',material_version:'old-v1'}];
 v.events[6].material_version='new-fomc-title';
 assert.ok(validateStockNovelty(v).errors.some(e=>e.startsWith('NO_NEW_FACT_FOR_OLD_STORY')));
});
test('a genuine earnings number change bound to new issuer source passes',()=>{
 const v=make();v.previous_events=[{event_key:'old-company',family_key:'stable-family-news-5',material_version:'guidance-previous'}];
 v.events[4].material_version='guidance-updated';
 v.events[4].novelty_proof={previous_material_version:'guidance-previous',changed_field:'company_guidance',old_value:'revenue $14 billion',new_value:'revenue $16 billion',evidence_url:'https://example.org/issuer/new-guidance',evidence_published_at:'2026-10-28T02:00:00Z'};
 v.items[4].text+=' revenue $16 billion';v.body=headings.map((h,i)=>h+'\n（1）'+v.items[i].text).join('\n\n');
 assert.equal(validateStockNovelty(v).passed,true);
});
test('changed metadata that is not actually explained in the email fails',()=>{
 const v=make();v.previous_events=[{family_key:'stable-family-news-5',material_version:'guidance-previous'}];
 v.events[4].material_version='guidance-updated';
 v.events[4].novelty_proof={previous_material_version:'guidance-previous',changed_field:'guidance',old_value:'old guidance',new_value:'new guidance',evidence_url:'https://example.org/new',evidence_published_at:'2026-10-28'};
 assert.ok(validateStockNovelty(v).errors.some(e=>e.startsWith('NO_NEW_FACT_FOR_OLD_STORY')));
});
test('same session observed twice is not new market movement',()=>{
 const v=make();v.previous_events=[{family_key:'stable-family-news-1',material_version:'other-time',observation_date:'2026-10-27'}];
 assert.ok(validateStockNovelty(v).errors.some(e=>e.startsWith('REPLAYED_MARKET_SESSION')));
});
test('future catalyst can only appear in calendar section',()=>{
 const v=make();v.items[8].section=8;
 assert.ok(validateStockNovelty(v).errors.some(e=>e.startsWith('CALENDAR_REPEATED_OUTSIDE_CALENDAR')));
});
test('local numbering must reset and be complete',()=>{
 const v=make();v.body=v.body.replace('二、正常时段、盘后与异动原因\n（1）','二、正常时段、盘后与异动原因\n（2）');
 assert.ok(validateStockNovelty(v).errors.some(e=>e.startsWith('NUMBERING')));
});
test('no seven-day Gmail review must be disclosed',()=>{
 const v=make();v.previous_days_checked=[];
 assert.ok(validateStockNovelty(v).warnings.includes('PREVIOUS_SEVEN_SENT_DAYS_NOT_PROVEN'));
});

test('IPO issuer pipeline receipt missing is a hard failure',()=>{
 const v=make();delete v.ipo_status_receipts;
 assert.ok(validateStockNovelty(v).errors.some(e=>e.startsWith('IPO_STATUS_SWEEP_MISSING')));
});
test('IPO source unavailable must be marked with reason, not no news',()=>{
 const v=make();v.ipo_status_receipts[0].new_delta_or_none='SOURCE_GAP';
 assert.ok(validateStockNovelty(v).errors.some(e=>e.startsWith('IPO_SOURCE_GAP_WITHOUT_REASON')));
});
test('scheduled X browser cannot claim original read without an actual tab',()=>{
 const v=make();v.x_source_receipt.status='ORIGINAL_READ';v.x_source_receipt.original_post_url='https://x.com/AnthropicAI/status/1234567890123456789';
 assert.ok(validateStockNovelty(v).errors.some(e=>e.startsWith('X_SOURCE_PROVENANCE_MISSING')));
});
test('public original X lookup is valid fallback when browser not connected',()=>{
 const v=make();assert.equal(validateStockNovelty(v).passed,true);
});
test('verified new IPO stage must appear in existing IPO section',()=>{
 const v=make();v.events[4].kind='IPO_ISSUER_STAGE';
 assert.ok(validateStockNovelty(v).errors.some(e=>e.startsWith('IPO_STAGE_NOT_IN_IPO_SECTION')));
});
