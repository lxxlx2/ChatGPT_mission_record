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
 async function submit(name,preset='quick',target=mint){
   await page.locator('#cluster-mint').fill(target);
   await page.locator('#cluster-preset').selectOption(preset);
   const reply=page.waitForResponse(r=>r.request().method()==='POST'&&r.url()===origin+'/api/cluster-analysis');
   await page.locator('#cluster-submit').click();
   const response=await reply;assert.equal(response.status(),202);
   const job=await response.json();
   if(name) await page.waitForFunction(label=>document.getElementById('cluster-summary').textContent.includes(label)&&!document.getElementById('cluster-submit').disabled,name);
   return job;
 }
 const a=await submit('SYNTHETIC_REPORT_1');
 const b=await submit('SYNTHETIC_REPORT_2','standard');
 assert.notEqual(a.job_id,b.job_id);
 check('quick/standard submit -> real worker persistence -> real report render');
 assert.equal(await page.locator('#cluster-reports option').count(),2);
 assert.match(await page.locator('#cluster-status').innerText(),/覆盖与完整性仍须另行核实/);
 await page.request.get(origin+'/__fixture/reset-memory');
 const postsBefore=requests.filter(r=>r.method==='POST').length;
 // A genuinely fresh page has no prior sessionStorage; recent completed report hints persist.
 await page.close();page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
 await page.goto(origin+'/#cluster');
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
 const submitting=submit(null,'deep','3'.repeat(32));
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
 check('deep DONE/report disconnect -> manual GET recovery -> real rendering and pending cleanup');
 await page.unroute('**/api/cluster-latest?*');
 const currentPosts=requests.filter(r=>r.method==='POST').length;
 await page.locator('#cluster-mint').fill('bad CA');await page.locator('#cluster-submit').click();
 assert.match(await page.locator('#cluster-status').innerText(),/完整.*Solana CA/);
 assert.equal(requests.filter(r=>r.method==='POST').length,currentPosts);
 check('invalid input is explained without submitting a scan');
 await page.locator('#cluster-mint').fill(mint);await page.locator('#cluster-read-cached').click();
 await page.waitForFunction(()=>document.getElementById('cluster-status').textContent.includes('与当前任务的关联未经核实'));
 assert.match(await page.locator('#cluster-status').innerText(),/覆盖仍不完整/);
 assert.equal(requests.filter(r=>r.method==='POST').length,currentPosts);
 check('visible existing-report entry reads partial historical cache without new POST');
 await submit(null,'quick','4'.repeat(32));
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
 const paused=await submit(null,'quick','3'.repeat(32));
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
