// Actual Chrome + actual product HTTP Handler/worker. Analyzer/RPC are synthetic.
// No production endpoints, wallets, keys or real scans. Browser profile is temporary.
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {mkdtempSync,rmSync,writeFileSync,mkdirSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createRequire} from 'node:module';
import {once} from 'node:events';
import {createConnection} from 'node:net';
const require=createRequire(import.meta.url);
const {chromium}=require(process.env.FRANK_PLAYWRIGHT_MODULE || 'playwright');
const root=mkdtempSync(join(tmpdir(),'frank-ca-browser-profile-'));
const output=process.env.FRANK_BROWSER_EVIDENCE;
if(output)mkdirSync(output,{recursive:true});
const python=process.env.FRANK_PYTHON || 'python3';
const env={PATH:process.env.PATH,LANG:'en_US.UTF-8',PYTHONDONTWRITEBYTECODE:'1'};
const child=spawn(python,['-I','-B',fileURLToPath(new URL('fixtures/frank_ca_browser_server.py',import.meta.url))],{env,stdio:['pipe','pipe','pipe']});
let context,port,stderr='',errors=[],blocked=[],requests=[],checks=[];
child.stderr.on('data',b=>{stderr+=b.toString();});
const exitPromise=once(child,'exit');
const timer=setTimeout(()=>{child.kill('SIGTERM');process.exitCode=1;},90000);
function check(name){checks.push(name);console.log('PASS '+name);}
async function snapshot(page,name){if(output){await page.screenshot({path:join(output,name+'.png'),fullPage:true});writeFileSync(join(output,name+'.txt'),await page.locator('#cluster-view').innerText());}}
try {
 const info=await Promise.race([once(child.stdout,'data').then(([b])=>JSON.parse(b.toString())),exitPromise.then(()=>{throw Error('fixture exited: '+stderr)}),new Promise((_,reject)=>setTimeout(()=>reject(Error('fixture startup timed out')),10000).unref())]);
 port=info.port;assert.notEqual(port,8766);assert.notEqual(port,8765);
 const origin='http://127.0.0.1:'+port;
 context=await chromium.launchPersistentContext(join(root,'profile'),{
   executablePath:process.env.FRANK_CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
   headless:true,serviceWorkers:'block',
   args:['--disable-background-networking','--disable-component-update','--disable-sync','--no-first-run','--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1']});
 await context.route('**/*',route=>{
   const req=route.request(),url=new URL(req.url());
   if(url.origin!==origin || !['GET','POST'].includes(req.method()) ||
      (req.method()==='POST'&&url.pathname!=='/api/cluster-analysis')){
     blocked.push({method:req.method(),kind:'OUTSIDE_FIXTURE'});return route.abort();
   }
   requests.push({method:req.method(),path:url.pathname,query:url.search});
   return route.continue();
 });
 let page=context.pages()[0];
 page.on('pageerror',e=>errors.push(e.message));
 await page.goto(origin+'/#cluster');
 await page.locator('#cluster-read-cached').waitFor({state:'visible'});
 await page.waitForFunction(()=>document.getElementById('updated').textContent.includes('更新于'));
 const mint='2'.repeat(32);
 async function submit(name,target=mint){
   await page.locator('#cluster-mint').fill(target);
   const reply=page.waitForResponse(r=>r.request().method()==='POST'&&r.url()===origin+'/api/cluster-analysis');
   await page.locator('#cluster-submit').click();
   const response=await reply;assert.equal(response.status(),202);
   const job=await response.json();
   assert.equal(job.preset,'standard');
   if(name) await page.waitForFunction(label=>document.getElementById('cluster-summary').textContent.includes(label)&&!document.getElementById('cluster-submit').disabled,name);
   return job;
 }
 assert.equal(await page.locator('#cluster-preset').count(),0);
 assert.match(await page.locator('#cluster-preset-help').innerText(),/统一查询/);
 check('single query entry removes depth selector and explains bounded incomplete evidence');
 const a=await submit('SYNTHETIC_REPORT_1');
 assert.equal(await page.locator('#cluster-rankings-panel').isVisible(),true);
 assert.match(await page.locator('#cluster-rankings').innerText(),/全局 Owner Top10/);
 assert.match(await page.locator('#cluster-rankings').innerText(),/98%/);
 assert.match(await page.locator('#cluster-rankings').innerText(),/20%/);
 assert.match(await page.locator('#cluster-rankings').innerText(),/本轮未覆盖历史/);
 const saved=await (await page.request.get(origin+'/api/cluster-latest?mint='+mint+'&job_id='+a.job_id)).json();
 assert.equal(saved.ca_job_id,a.job_id);
 assert.equal(saved.narrative.official_recognition,'UNVERIFIED');
 assert.equal(saved.market.comparison.status,'INDEXER_SNAPSHOTS_COMPARED');
 assert.match(await page.locator('.cluster-market-comparison').innerText(),/25.0000%/);
 assert.match(await page.locator('.cluster-market-comparison').innerText(),/未核对链上池子储备/);
 check('same-pool indexer differences persist with source times and no chain parity claim');
 assert.equal(saved.analysis_completeness.status,'INCOMPLETE_EVIDENCE');
 assert.ok(saved.analysis_completeness.missing_required.includes('narrative'));
 assert.ok(saved.analysis_completeness.missing_required.includes('wallet_history'));
 assert.match(await page.locator('#cluster-completeness').innerText(),/证据不完整/);
 await page.locator('#cluster-completeness summary').click();
 assert.match(await page.locator('#cluster-completeness').innerText(),/完整历史/);
 assert.match(await page.locator('#cluster-completeness').innerText(),/外部叙事/);
 assert.match(await page.locator('#cluster-completeness').innerText(),/下一来源/);
 assert.match(await page.locator('#cluster-status').innerText(),/证据不完整/);
 await page.locator('#cluster-completeness summary').click();
 check('worker DONE persists incomplete product outcome and browser shows required evidence gaps');
 check('full mint Owner ranks are separate from raw Top20 history and preserve uncovered history');
 await page.locator('.cluster-detail-fold > summary').click();
 assert.equal(await page.locator('#cluster-narrative').isVisible(),true);
 assert.match(await page.locator('#cluster-narrative').innerText(),/A fictional cat/);
 assert.match(await page.locator('#cluster-narrative').innerText(),/精确 CA 未提及/);
 assert.match(await page.locator('#cluster-narrative').innerText(),/官方归属未核实/);
 check('external narrative claim persists without exact-CA endorsement or invented publication time');

 await page.locator('.cluster-historical-accounts summary').click();
 assert.match(await page.locator('.cluster-historical-accounts').innerText(),/该交易结束时关闭/);
 assert.match(await page.locator('.cluster-historical-accounts').innerText(),/不能证明当前仍关闭/);
 assert.match(await page.locator('.cluster-historical-accounts').innerText(),/本轮只补查一轮/);
 assert.equal(saved.historical_account_evidence[0].signature,'FIXTURE_HISTORICAL_PROOF');
 check('historical Owner, closure time and one-frontier gap persist without current ownership claims');
 await page.locator('.cluster-historical-accounts summary').click();
 await page.locator('.cluster-owner-accounts summary').click();
 assert.match(await page.locator('.cluster-owner-accounts').innerText(),/本轮额外账户上限/);
 assert.match(await page.locator('.cluster-owner-accounts').innerText(),/已关闭账户.*未枚举/);
 assert.ok(saved.coverage.owner_account_history[0].accounts_selected.length===2);
 check('persisted Owner account selection, limits and missing closed history remain explicit');
 await page.locator('.cluster-owner-accounts summary').click();
 await page.locator('.cluster-history-windows summary').click();
 assert.match(await page.locator('#cluster-coverage').innerText(),/目标币账户历史/);
 assert.match(await page.locator('#cluster-coverage').innerText(),/达到本轮页数上限/);
 assert.match(await page.locator('#cluster-coverage').innerText(),/来源空页也不证明完整钱包历史/);
 check('bounded history pages and cursor are visible without claiming full wallet history');
 await page.locator('.cluster-detail-fold > summary').click();
 const b=await submit('SYNTHETIC_REPORT_2');
 assert.notEqual(a.job_id,b.job_id);
 check('single-mode submits -> distinct real worker persistence -> real report render');
 assert.equal(await page.locator('#cluster-reports option').count(),2);
 assert.match(await page.locator('#cluster-status').innerText(),/覆盖与完整性仍须另行核实/);
 await page.request.get(origin+'/__fixture/reset-memory');
 const postsBefore=requests.filter(r=>r.method==='POST').length;
 // A genuinely fresh page has no prior sessionStorage; recent completed report hints persist.
 await page.close();page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
 await page.goto(origin+'/#cluster');
 await page.waitForFunction(()=>document.getElementById('cluster-status').textContent.includes('已读取已有历史报告')&&!document.getElementById('cluster-result').hidden);
 assert.match(await page.locator('#cluster-status').innerText(),/与当前任务的关联未经核实/);
 assert.match(await page.locator('#cluster-summary').innerText(),/SYNTHETIC_REPORT_2/);
 assert.equal(await page.locator('#cluster-mint').inputValue(),mint);
 assert.equal(requests.filter(r=>r.method==='POST').length,postsBefore);
 check('fresh page automatic history read is explicitly unverified and GET only');
 await page.locator('#cluster-reports').selectOption(a.job_id);
 await page.locator('#cluster-read-report').click();
 await page.waitForFunction(()=>document.getElementById('cluster-summary').textContent.includes('SYNTHETIC_REPORT_1')&&!document.getElementById('cluster-submit').disabled);
 assert.equal(requests.filter(r=>r.method==='POST').length,postsBefore);
 check('new page + empty backend memory -> select original A instead of latest B, GET only');
 await snapshot(page,'original-A-recovered');
 // Interrupt exactly the first report GET for the next real fixture submission.
 let failures=0;
 await page.route('**/api/cluster-latest?*',route=>{if(route.request().url().includes('job_id=')&&failures++===0)return route.abort('connectionreset');return route.fallback();});
 let releasePost,postArrived;
 const postGate=new Promise(resolve=>{releasePost=resolve;});
 const postSeen=new Promise(resolve=>{postArrived=resolve;});
 const postPattern='**/api/cluster-analysis';
 await page.route(postPattern,async route=>{postArrived();await postGate;return route.fallback();});
 const submitting=submit(null,'3'.repeat(32));
 await postSeen;
 try {
   assert.equal(await page.locator('#cluster-read-cached').isDisabled(),true);
   assert.equal(await page.locator('#cluster-read-report').isDisabled(),true);
   const before=requests.length;
   await page.evaluate(()=>{
     for(const id of ['cluster-read-cached','cluster-read-report'])
       document.getElementById(id).dispatchEvent(new MouseEvent('click'));
   });
   assert.equal(requests.length,before);
 } finally { releasePost(); }
 const c=await submitting;
 await page.unroute(postPattern);
 check('history controls during pending POST cannot discard the acknowledged job');
 await page.getByRole('button',{name:'重试读取报告',exact:true}).waitFor({state:'visible'});
 await page.waitForFunction(()=>document.getElementById('cluster-status').textContent.includes('报告读取中断'));
 const pending=await page.evaluate(()=>sessionStorage.getItem('mission-meme-cluster-pending-v1'));
 assert.equal(JSON.parse(pending).id,c.job_id);
 const retryPosts=requests.filter(r=>r.method==='POST').length;
 const savedPattern='**/api/cluster-latest?*job_id='+a.job_id;
 await page.route(savedPattern,route=>route.abort('connectionreset'));
 await page.locator('#cluster-reports').selectOption(a.job_id);
 await page.locator('#cluster-read-report').click();
 await page.waitForFunction(()=>document.getElementById('cluster-status').textContent.includes('选中报告读取或核对失败'));
 assert.equal(await page.evaluate(()=>sessionStorage.getItem('mission-meme-cluster-pending-v1')),pending);
 assert.equal(await page.locator('#cluster-result').isVisible(),false);
 await page.unroute(savedPattern);
 check('failed saved-report read preserves the other pending job');
 await page.locator('#cluster-read-report').click();
 await page.waitForFunction(()=>document.getElementById('cluster-result').hidden===false&&document.getElementById('cluster-status').textContent.includes('已读取该任务保存报告'));
 assert.match(await page.locator('#cluster-summary').innerText(),/SYNTHETIC_REPORT_1/);
 assert.equal(await page.evaluate(()=>sessionStorage.getItem('mission-meme-cluster-pending-v1')),pending);
 assert.equal(await page.locator('#cluster-mint').inputValue(),mint);
 check('view saved A while C awaits recovery without replacing C');
 await page.getByRole('button',{name:'重试读取报告',exact:true}).click();
 await page.waitForFunction(()=>document.getElementById('cluster-summary').textContent.includes('SYNTHETIC_REPORT_3')&&!document.getElementById('cluster-submit').disabled);
 assert.equal(await page.evaluate(()=>sessionStorage.getItem('mission-meme-cluster-pending-v1')),null);
 assert.equal(await page.locator('#cluster-mint').inputValue(),'3'.repeat(32));
 assert.equal(requests.filter(r=>r.method==='POST').length,retryPosts);
 check('unified DONE/report disconnect -> manual GET recovery -> real rendering and pending cleanup');
 await page.unroute('**/api/cluster-latest?*');
 const currentPosts=requests.filter(r=>r.method==='POST').length;
 await page.locator('#cluster-mint').fill('bad CA');await page.locator('#cluster-submit').click();
 assert.match(await page.locator('#cluster-status').innerText(),/完整.*Solana CA/);
 assert.equal(requests.filter(r=>r.method==='POST').length,currentPosts);
 check('invalid input is explained without submitting a scan');
 await page.locator('#cluster-mint').fill(mint);await page.locator('#cluster-read-cached').click();
 await page.waitForFunction(()=>document.getElementById('cluster-status').textContent.includes('已读取已有历史报告')&&!document.getElementById('cluster-result').hidden);
 assert.match(await page.locator('#cluster-status').innerText(),/与当前任务的关联未经核实/);
 assert.match(await page.locator('#cluster-status').innerText(),/覆盖仍不完整/);
 assert.equal(requests.filter(r=>r.method==='POST').length,currentPosts);
 check('visible existing-report entry reads partial historical cache without new POST');
 const missingMint='5'.repeat(32);
 await page.locator('#cluster-mint').fill(missingMint);
 await page.locator('#cluster-read-cached').click();
 await page.waitForFunction(()=>document.getElementById('cluster-status').textContent.includes('历史缓存读取失败'));
 assert.equal(await page.locator('#cluster-result').isVisible(),false);
 assert.equal(await page.locator('#cluster-preview').isVisible(),false);
 assert.equal(await page.locator('#cluster-mint').inputValue(),missingMint);
 assert.equal(requests.filter(r=>r.method==='POST').length,currentPosts);
 check('missing history for another CA hides the old report without a new POST');
 await submit(null,'4'.repeat(32));
 await page.waitForFunction(()=>document.getElementById('cluster-status').textContent.includes('分析任务失败'));
 assert.equal(await page.locator('#cluster-result').isVisible(),false);
 check('worker error remains error, no phantom successful report');
 await page.locator('#cluster-clear-reports').click();
 assert.equal(await page.locator('#cluster-read-report').isDisabled(),true);
 assert.equal(await page.evaluate(()=>localStorage.getItem('mission-meme-cluster-reports-v1')),null);
 check('local report shortcuts can be cleared without changing backend reports');
 // Optional browser persistence may be blocked by privacy settings. Exercise
 // the complete app boot, POST acknowledgement and DONE recovery in that case.
 const regularPage=page;
 page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
 await page.addInitScript(()=>Object.defineProperty(window,'localStorage',{
   get(){throw new DOMException('Fixture storage access denied','SecurityError');}
 }));
 await page.goto(origin+'/#cluster');
 await page.locator('#cluster-read-cached').waitFor({state:'visible'});
 let storageFailures=0;
 await page.route('**/api/cluster-latest?*',route=>{
   if(route.request().url().includes('job_id=')&&storageFailures++===0)return route.abort('connectionreset');
   return route.fallback();
 });
 const noStorage=await submit(null);
 await page.getByRole('button',{name:'重试读取报告',exact:true}).waitFor({state:'visible'});
 await page.waitForFunction(()=>document.getElementById('cluster-status').textContent.includes('报告读取中断'));
 assert.equal(JSON.parse(await page.evaluate(()=>sessionStorage.getItem('mission-meme-cluster-pending-v1'))).id,noStorage.job_id);
 const noStoragePosts=requests.filter(r=>r.method==='POST').length;
 await page.getByRole('button',{name:'重试读取报告',exact:true}).click();
 await page.waitForFunction(()=>document.getElementById('cluster-summary').textContent.includes('SYNTHETIC_REPORT_5')&&!document.getElementById('cluster-submit').disabled);
 assert.equal(await page.evaluate(()=>sessionStorage.getItem('mission-meme-cluster-pending-v1')),null);
 assert.equal(requests.filter(r=>r.method==='POST').length,noStoragePosts);
 check('blocked localStorage still permits app boot, acknowledged job and GET-only DONE recovery');
 await page.close();page=regularPage;
 // A user can edit the CA while the server's POST receipt is still in flight.
 let releaseEditedPost,editedPostSeen;
 const editedPostGate=new Promise(resolve=>{releaseEditedPost=resolve;});
 const editedPostArrived=new Promise(resolve=>{editedPostSeen=resolve;});
 await page.route(postPattern,async route=>{editedPostSeen();await editedPostGate;return route.fallback();});
 const editedSubmit=submit(null);
 await editedPostArrived;
 try {await page.locator('#cluster-mint').fill('3'.repeat(32));}
 finally {releaseEditedPost();}
 await editedSubmit;
 await page.unroute(postPattern);
 assert.equal(await page.locator('#cluster-mint').inputValue(),mint);
 await page.waitForFunction(()=>document.getElementById('cluster-summary').textContent.includes('SYNTHETIC_REPORT_6')&&!document.getElementById('cluster-submit').disabled);
 check('edited input during POST is restored to the acknowledged job CA');
 // Pause a RUNNING task with a slow historical GET, then edit the input.
 // Discarding that stale response must still expose the paused original task.
 const paused=await submit(null,'3'.repeat(32));
 await page.waitForFunction(()=>/等待开始分析|正在扫描链上数据/.test(document.getElementById('cluster-status').textContent));
 let releaseHistory,historySeen;
 const historyGate=new Promise(resolve=>{releaseHistory=resolve;});
 const historyArrived=new Promise(resolve=>{historySeen=resolve;});
 const historyPattern=origin+'/api/cluster-latest?mint='+'3'.repeat(32);
 await page.route(historyPattern,async route=>{historySeen();await historyGate;return route.fallback();});
 await page.locator('#cluster-read-cached').click();
 await historyArrived;
 try {await page.locator('#cluster-mint').fill(mint);}
 finally {releaseHistory();}
 await page.locator('#cluster-recovery').waitFor({state:'visible'});
 await page.unroute(historyPattern);
 assert.equal(JSON.parse(await page.evaluate(()=>sessionStorage.getItem('mission-meme-cluster-pending-v1'))).id,paused.job_id);
 const pausedPosts=requests.filter(r=>r.method==='POST').length;
 await page.getByRole('button',{name:'继续读取原任务',exact:true}).click();
 await page.waitForFunction(()=>document.getElementById('cluster-summary').textContent.includes('SYNTHETIC_REPORT_7')&&!document.getElementById('cluster-submit').disabled);
 assert.equal(await page.locator('#cluster-mint').inputValue(),'3'.repeat(32));
 assert.equal(requests.filter(r=>r.method==='POST').length,pausedPosts);
 check('edited input during historical GET leaves the paused task reachable and recoverable');
 // The integrated source must preserve D2 manual loading and its local age
 // updates while the CA recovery code and source-only F01 refresh coexist.
 const d2ReadsBefore=requests.filter(r=>r.path==='/api/frank-d2-at-slot').length;
 assert.equal(d2ReadsBefore,0,'CA navigation must not auto-read D2');
 const combinedPosts=requests.filter(r=>r.method==='POST').length;
 await page.getByRole('button',{name:'Frank 信号',exact:true}).click();
 await page.waitForFunction(()=>document.getElementById('f01-source-status').textContent.includes('近期'));
 await page.locator('#frank-d2-read').click();
 await page.waitForFunction(()=>document.getElementById('frank-d2-rows').textContent.includes('12 枚'));
 assert.match(await page.locator('#frank-d2-summary').innerText(),/非原子快照/);
 const ageBefore=await page.locator('#frank-d2-summary').innerText();
 await page.waitForFunction(before=>document.getElementById('frank-d2-summary').textContent!==before,ageBefore,{timeout:10000});
 assert.match(await page.locator('#frank-d2-rows').innerText(),/12 枚/);
 assert.equal(requests.filter(r=>r.path==='/api/frank-d2-at-slot').length,d2ReadsBefore+1);
 assert.equal(requests.filter(r=>r.method==='POST').length,combinedPosts);
 await page.getByRole('button',{name:'CA 链上查询',exact:true}).click();
 assert.match(await page.locator('#cluster-summary').innerText(),/SYNTHETIC_REPORT_7/);
 check('combined CA/F01/D2 preserves manual snapshot reads, local source age and CA report');

 // Fault injection is confined to the CI fixture origin. Existing five-second
 // refresh performs recovery; no new timer, retry loop or scan is introduced.
 await page.getByRole('button',{name:'Frank 信号',exact:true}).click();
 const candidatesPattern=origin+'/api/candidates';
 for (const phase of ['NETWORK','JSON','HTTP']) {
   const failurePosts=requests.filter(r=>r.method==='POST').length;
   await page.route(candidatesPattern,route=>{
     if(phase==='NETWORK')return route.abort('connectionreset');
     return route.fulfill({status:phase==='HTTP'?503:200,
       contentType:'application/json',body:'private-fixture-body-token=fixture-secret'});
   });
   await page.waitForFunction(expected=>document.getElementById('runtime').textContent.includes('['+expected+']'),phase,{timeout:10000});
   const failedRuntime=await page.locator('#runtime').innerText();
   assert.match(failedRuntime,/GET \/api\/candidates/);
   assert.doesNotMatch(failedRuntime,/fixture-secret|private-fixture|Failed to fetch|SyntaxError/);
   assert.match(await page.locator('#f01-source-status').innerText(),/不展示可跟结论/);
   assert.equal(await page.locator('#candidates .candidate-card').count(),0);
   assert.match(await page.locator('#frank-d2-rows').innerText(),/12 枚/);
   assert.equal(requests.filter(r=>r.method==='POST').length,failurePosts);
   await snapshot(page,'safe-get-'+phase.toLowerCase());
   await page.unroute(candidatesPattern);
   await page.waitForFunction(()=>!document.getElementById('runtime').textContent.includes('控制台读取失败')&&document.getElementById('f01-source-status').textContent.includes('近期'),null,{timeout:10000});
   assert.equal(requests.filter(r=>r.method==='POST').length,failurePosts);
   check('GET '+phase+' is safely attributed, closes old F01 cards and recovers without POST');
 }
 await page.getByRole('button',{name:'CA 链上查询',exact:true}).click();
 assert.match(await page.locator('#cluster-summary').innerText(),/SYNTHETIC_REPORT_7/);

 // Overlapping observation refreshes must not replace a newer SELL with
 // an older BUY, nor resurrect cached rows when the user filters after failure.
 await page.getByRole('button',{name:'Frank 信号',exact:true}).click();
 await page.locator('#frank-activity-type').selectOption({label:'全部买卖'});
 const observationFeeds=[
   {kind:'intelligence',endpoint:'/api/frank-intelligence',reload:'frank-intelligence-reload',
    root:'frank-intelligence-cards',filter:'frank-intelligence-search',updated:'frank-intelligence-updated'},
   {kind:'activity',endpoint:'/api/frank-activity-watch',reload:'frank-activity-reload',
    root:'frank-activity-feed',filter:'frank-activity-search',updated:'frank-activity-updated'},
 ];
 function observationPayload(kind,target,side) {
   return kind==='intelligence'
     ? {status:'LOCAL_SOURCE_RESEARCH_ONLY',rows:[{mint:target,latest_side:side,
         latest_action_at:1,source_signal_id:'FIXTURE_'+side,facts:[],missing:[],price:{}}]}
     : {status:'LOCAL_SOURCE_ACTIVITY_RESEARCH_ONLY',source_rows_considered:1,counts:{},
         rows:[{mint:target,source_side:side,signature:'5'.repeat(64),block_time:1}]};
 }
 for(const feed of observationFeeds) {
   const beforePosts=requests.filter(r=>r.method==='POST').length;
   const endpoint=origin+feed.endpoint,newerMint='3'.repeat(32);
   let releaseOld,oldArrived,calls=0;
   const oldGate=new Promise(resolve=>{releaseOld=resolve;});
   const oldSeen=new Promise(resolve=>{oldArrived=resolve;});
   await page.locator('#'+feed.filter).fill('');
   await page.route(endpoint,async route=>{
     if(++calls===1) {
       oldArrived();await oldGate;
       return route.fulfill({status:200,contentType:'application/json',
         headers:{'X-Fixture-Response':'OLDER_BUY'},
         body:JSON.stringify(observationPayload(feed.kind,mint,'BUY'))});
     }
     return route.fulfill({status:200,contentType:'application/json',
       body:JSON.stringify(observationPayload(feed.kind,newerMint,'SELL'))});
   });
   await page.locator('#'+feed.reload).click();
   await oldSeen;
   await page.locator('#'+feed.reload).click();
   await page.waitForFunction(({root,target})=>document.getElementById(root).innerHTML.includes(target),
     {root:feed.root,target:newerMint});
   const oldReply=page.waitForResponse(r=>r.url()===endpoint&&r.headers()['x-fixture-response']==='OLDER_BUY');
   releaseOld();
   await (await oldReply).finished();
   await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
   assert.equal(await page.locator('#'+feed.root+' [data-copy]').first().getAttribute('data-copy'),newerMint);
   await page.locator('#'+feed.filter).fill(newerMint);
   assert.equal(await page.locator('#'+feed.root+' [data-copy]').first().getAttribute('data-copy'),newerMint);
   assert.equal(requests.filter(r=>r.method==='POST').length,beforePosts);
   await snapshot(page,'observation-'+feed.kind+'-newer-sell-retained');
   await page.unroute(endpoint);
   check(feed.kind+' keeps newer SELL and filter snapshot after delayed older BUY');
 }
 const intelligence=observationFeeds[0],intelEndpoint=origin+intelligence.endpoint;
 const filterFailurePosts=requests.filter(r=>r.method==='POST').length;
 await page.locator('#'+intelligence.filter).fill('');
 await page.route(intelEndpoint,route=>route.fulfill({status:200,contentType:'application/json',
   body:JSON.stringify(observationPayload('intelligence',mint,'BUY'))}));
 await page.locator('#'+intelligence.reload).click();
 await page.waitForFunction(target=>document.getElementById('frank-intelligence-cards').innerHTML.includes(target),mint);
 await page.unroute(intelEndpoint);
 await page.route(intelEndpoint,route=>route.fulfill({status:503,contentType:'application/json',body:'{}'}));
 await page.locator('#'+intelligence.reload).click();
 await page.waitForFunction(()=>document.getElementById('frank-intelligence-updated').textContent==='来源不可用');
 await page.locator('#'+intelligence.filter).fill(mint);
 assert.equal(await page.locator('#frank-intelligence-cards article').count(),0);
 assert.match(await page.locator('#frank-intelligence-summary').innerText(),/来源不可用/);
 assert.match(await page.locator('#frank-d2-rows').innerText(),/12 枚/);
 assert.equal(requests.filter(r=>r.method==='POST').length,filterFailurePosts);
 await snapshot(page,'intelligence-failed-refresh-filter-remains-unavailable');
 await page.unroute(intelEndpoint);
 check('intelligence filter cannot resurrect cached BUY after failed refresh; D2 remains independent');
 await page.getByRole('button',{name:'CA 链上查询',exact:true}).click();
 assert.match(await page.locator('#cluster-summary').innerText(),/SYNTHETIC_REPORT_7/);
 assert.deepEqual(errors,[]);
 const result={port,checks,page_errors:errors,blocked,requests,fixture_posts:requests.filter(r=>r.method==='POST').length,real_rpc:0,production_requests:0,real_ca_posts:0,browser:context.browser()?.version()};
 if(output)writeFileSync(join(output,'result.json'),JSON.stringify(result,null,2));
 console.log(JSON.stringify(result));
} finally {
 clearTimeout(timer);
 if(context)await context.close();
 child.stdin.end();
 await Promise.race([exitPromise,new Promise(resolve=>setTimeout(()=>{child.kill('SIGTERM');resolve();},5000).unref())]);
 rmSync(root,{recursive:true,force:true});
 if(port){const listening=await new Promise(resolve=>{const s=createConnection({host:'127.0.0.1',port});s.on('connect',()=>{s.destroy();resolve(true)});s.on('error',()=>resolve(false));});assert.equal(listening,false,'fixture port released');}
 console.log('CLEANUP: browser profile removed, fixture exited, port released');
}

