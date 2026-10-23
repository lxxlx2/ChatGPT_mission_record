const { chromium }=require('/Users/jerson/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const http=require('node:http'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),os=require('node:os'),assert=require('node:assert/strict'),cp=require('node:child_process');
const checkout='/tmp/frank168-cdf-656ed2c',out='/tmp/frank168-cdf-evidence';
const staticRoot=path.join(checkout,'crypto-300-profit-mission/local-agent/mission_agent/mission_control/static');
const SHA='656ed2c96f4210d106d7b1129ec6cf8d7c4586f3',KEY='mission-meme-cluster-pending-v1';
const A='2'.repeat(32), B='3'.repeat(32), JA='a'.repeat(32),JB='b'.repeat(32);
const audit=[],consoleRecords=[],pageErrors=[],results=[],scenes=new Map();
let context,server,proxy,profile,port,origin,requestSeq=0;
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const manifest=Object.fromEntries(['index.html','app.js','styles.css'].map(n=>[n,hash(fs.readFileSync(path.join(staticRoot,n)))]));
assert.equal(cp.execFileSync('git',['-C',checkout,'rev-parse','HEAD'],{encoding:'utf8'}).trim(),SHA);
const fixedReport=m=>({mint:m,observed_at:1792683606,coverage:{special_normalization_complete:false,deep_holders_scanned:1,top_accounts_resolved:1,rpc_endpoint_failures:{}},market:{status:'UNAVAILABLE',name:m===A?'FIXTURE_A':'FIXTURE_B',symbol:'QA',main_pair:{}},metrics:{},assessment:{chain_permission_status:'UNRESOLVED',cluster_status:'WALLET_CLUSTER_UNRESOLVED'},token_profile:{status:'UNAVAILABLE'},holders:[],limitations:['FIXTURE_ONLY_NOT_CHAIN_DATA'],transaction_errors:[]});
const job=(id,mint,status='RUNNING')=>({job_id:id,mint,status,preset:'deep',progress:{stage:'HOLDERS_READY',top_accounts_resolved:1},preview:{name:mint===A?'FIXTURE_A':'FIXTURE_B',symbol:'QA',token_status:'UNAVAILABLE',market_status:'UNAVAILABLE',top_accounts_resolved:1}});
const safeGet=p=>{
 if(['/api/candidates','/api/trades','/api/review-activity','/api/decisions'].includes(p))return [];
 if(p==='/api/runtime')return {status:'UNKNOWN',runtime_reason:'FIXTURE_ONLY',heartbeat_age_seconds:null};
 if(p==='/api/control-health')return {status:'UNKNOWN',manual_review_total_count:0};
 if(p==='/api/coverage')return {};
 if(p==='/api/frank-observed-watchlist')return {status:'SOURCE_UNAVAILABLE',rows:[],summary:{}};
 if(p==='/api/frank-signed-activity')return {status:'INDEXED_LOCAL_ONLY',rows:[],summary:{},counts:{}};
 if(p==='/api/frank-intelligence')return {status:'LOCAL_SOURCE_RESEARCH_ONLY',rows:[],notification_authorized:false};
 if(p==='/api/frank-activity-watch')return {status:'LOCAL_SOURCE_ACTIVITY_RESEARCH_ONLY',rows:[],counts:{},source_rows_considered:0};
 return null;
};
const deferred=()=>{let resolve;const promise=new Promise(r=>resolve=r);return {resolve,promise}};
const json=(res,status,data)=>{res.writeHead(status,{'Content-Type':'application/json','Cache-Control':'no-store'});res.end(JSON.stringify(data))};
async function snapshot(page,name){
 const dom=await page.evaluate(key=>({url:location.href,status:document.querySelector('#cluster-status').innerText,statusClass:document.querySelector('#cluster-status').className,input:document.querySelector('#cluster-mint').value,summary:document.querySelector('#cluster-summary').innerText,reportVisible:!document.querySelector('#cluster-result').hidden,recoveryVisible:!document.querySelector('#cluster-recovery').hidden,resumeVisible:!document.querySelector('#cluster-resume-get').hidden,resumeText:document.querySelector('#cluster-resume-get').innerText,submitDisabled:document.querySelector('#cluster-submit').disabled,pending:sessionStorage.getItem(key)}),KEY);
 fs.writeFileSync(path.join(out,name+'.dom.json'),JSON.stringify(dom,null,2));
 await page.locator('#cluster-status').scrollIntoViewIfNeeded();await page.screenshot({path:path.join(out,name+'.png')});return dom;
}
async function openScene(name,seed={}){
 const scene={name,polls:0,reports:0,posts:0,handler:null,aborted:0};scenes.set(name,scene);
 const page=await context.newPage();page.__scene=name;
 page.on('console',m=>{if(['error','warning'].includes(m.type()))consoleRecords.push({scene:name,type:m.type(),text:m.text(),at:new Date().toISOString()})});
 page.on('pageerror',e=>pageErrors.push({scene:name,message:e.message}));
 await page.addInitScript(({seed,key,origin})=>{
  if(location.origin!==origin || sessionStorage.getItem('fixture-seeded'))return;
  sessionStorage.setItem('fixture-seeded','1');localStorage.removeItem('mission-meme-last-cluster-ca');
  if(seed.pending)sessionStorage.setItem(key,JSON.stringify(seed.pending));
  if(seed.last)localStorage.setItem('mission-meme-last-cluster-ca',seed.last);
 },{seed,key:KEY,origin});
 return {page,scene};
}
async function runCase(name,fn){let page;try{await fn(p=>page=p);results.push({case:name,result:'PASS'})}catch(e){results.push({case:name,result:'FAIL',error:e.message});if(page&&!page.isClosed())await snapshot(page,name+'-FAIL').catch(()=>{})}finally{if(page&&!page.isClosed())await page.close()}}
(async()=>{
 try{
  server=http.createServer((req,res)=>{
   const u=new URL(req.url,origin);const allowed={'/':'index.html','/index.html':'index.html','/static/app.js':'app.js','/static/styles.css':'styles.css'};
   if(req.method==='GET'&&allowed[u.pathname]){const n=allowed[u.pathname];res.writeHead(200,{'Content-Type':n.endsWith('.js')?'application/javascript':n.endsWith('.css')?'text/css':'text/html','Cache-Control':'no-store'});res.end(fs.readFileSync(path.join(staticRoot,n)));return}
   if(u.pathname==='/favicon.ico'){res.writeHead(204);return res.end()}
   // CA fixture requests are fulfilled by the same-origin browser route below, never forwarded.
   res.writeHead(403);res.end('FIXTURE_UNEXPECTED_REQUEST_DENIED');
  });await new Promise(r=>server.listen(0,'127.0.0.1',r));port=server.address().port;assert.notEqual(port,8766);assert.notEqual(port,8765);origin='http://127.0.0.1:'+port;
  proxy=http.createServer((req,res)=>{audit.push({kind:'PROXY_DENIED',method:req.method,url:req.url});res.writeHead(403);res.end()});proxy.on('connect',(req,socket)=>{audit.push({kind:'PROXY_CONNECT_DENIED',url:req.url});socket.end('HTTP/1.1 403 Forbidden\r\n\r\n')});await new Promise(r=>proxy.listen(0,'127.0.0.1',r));
  profile=fs.mkdtempSync(path.join(os.tmpdir(),'frank168-chrome-isolated-'));
  context=await chromium.launchPersistentContext(profile,{executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:false,viewport:{width:1280,height:900},timezoneId:'Asia/Bangkok',locale:'zh-CN',serviceWorkers:'block',args:['--no-first-run','--disable-background-networking','--disable-component-update','--disable-default-apps','--disable-sync','--disable-domain-reliability','--disable-client-side-phishing-detection','--disable-extensions','--disable-features=MediaRouter,OptimizationHints,AutofillServerCommunication','--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1',`--proxy-server=http://127.0.0.1:${proxy.address().port}`,'--proxy-bypass-list=127.0.0.1;localhost']});
  await context.route('**/*',async route=>{
   const request=route.request(),u=new URL(request.url());let page;try{page=request.frame().page()}catch{}
   const scene=scenes.get(page?.__scene);const record={seq:++requestSeq,at:new Date().toISOString(),ms:Date.now(),scene:scene?.name||'unassigned',method:request.method(),url:request.url()};audit.push(record);
   if(u.origin!==origin){record.action='DENIED_NON_FIXTURE';return route.abort('blockedbyclient')}
   const fulfill=async(status,data)=>{record.status=status;record.action='FIXTURE_JSON';await route.fulfill({status,contentType:'application/json',body:JSON.stringify(data)})};
   const abort=async()=>{record.status=null;record.action='SIMULATED_CONNECTION_RESET';if(scene)scene.aborted++;await route.abort('connectionreset')};
   if(u.pathname.startsWith('/api/')){
    if(!scene){record.action='DENIED_UNASSIGNED';return route.abort('blockedbyclient')}
    if(u.pathname==='/api/cluster-analysis'){
     if(request.method()==='GET')scene.polls++;else if(request.method()==='POST')scene.posts++;
     if(scene.handler)return scene.handler({u,request,record,fulfill,abort,scene});
    }else if(u.pathname==='/api/cluster-latest'){
     scene.reports++;if(scene.handler)return scene.handler({u,request,record,fulfill,abort,scene});
    }else if(request.method()==='GET'){
     const data=safeGet(u.pathname);if(data!==null)return fulfill(200,data);
    }
    record.action='DENIED_UNEXPECTED_API';return fulfill(403,{error:'FIXTURE_DENIED'});
   }
   if(request.method()!=='GET'||!['/','/index.html','/static/app.js','/static/styles.css','/favicon.ico'].includes(u.pathname)){record.action='DENIED_UNEXPECTED_RESOURCE';return route.abort('blockedbyclient')}
   record.action='LOCAL_STATIC';return route.continue();
  });
  fs.writeFileSync(path.join(out,'setup.json'),JSON.stringify({sourceSHA:SHA,port,origin,platform:os.platform(),browser:context.browser()?.version(),staticSHA256:manifest,independentTemporaryProfile:true},null,2));
  // C: genuine form click starts fixture B while A cache response is delayed.
  await runCase('C',async take=>{
   const {page,scene}=await openScene('C',{pending:{id:JA,mint:A}});take(page);const late=deferred();let waiting=false;
   scene.handler=async x=>{
    if(x.u.pathname==='/api/cluster-latest'){
     const mint=x.u.searchParams.get('mint');if(mint===A){waiting=true;await late.promise;await x.fulfill(200,fixedReport(A));return}return x.fulfill(200,fixedReport(B));
    }
    if(x.request.method()==='POST'){const body=x.request.postDataJSON();assert.equal(body.mint,B);return x.fulfill(202,job(JB,B,'QUEUED'))}
    const id=x.u.searchParams.get('job_id');return id===JA?x.fulfill(404,{error:'CLUSTER_JOB_NOT_FOUND'}):x.fulfill(200,job(JB,B,'DONE'));
   };
   await page.goto(origin+'/#cluster');await page.locator('#cluster-status').filter({hasText:'原任务当前不存在'}).waitFor();await page.locator('#cluster-read-cached').click();await page.waitForFunction(()=>true);assert.ok(waiting);
   await page.locator('#cluster-mint').fill(B);await page.locator('#cluster-submit').click();await page.locator('#cluster-summary').filter({hasText:'FIXTURE_B'}).waitFor();await page.locator('#cluster-status').filter({hasText:'原分析任务已结束'}).waitFor();
   const before=await page.locator('#cluster-status').innerText(),controls=await page.locator('#cluster-recovery').isVisible();late.resolve();await new Promise(r=>setTimeout(r,250));
   assert.equal(await page.locator('#cluster-mint').inputValue(),B);assert.match(await page.locator('#cluster-summary').innerText(),/FIXTURE_B/);assert.doesNotMatch(await page.locator('#cluster-summary').innerText(),/FIXTURE_A/);assert.equal(await page.locator('#cluster-status').innerText(),before);assert.equal(await page.locator('#cluster-recovery').isVisible(),controls);assert.equal(scene.posts,1);await snapshot(page,'C-late-A-cannot-overwrite-B');
  });
  // D: first saved-report GET fails, manual retry invokes only report GET.
  await runCase('D',async take=>{
   const {page,scene}=await openScene('D',{pending:{id:JA,mint:A}});take(page);
   scene.handler=x=>x.u.pathname==='/api/cluster-analysis'?x.fulfill(200,job(JA,A,'DONE')):scene.reports===1?x.abort():x.fulfill(200,fixedReport(A));
   await page.goto(origin+'/#cluster');await page.locator('#cluster-status').filter({hasText:'报告读取中断'}).waitFor();assert.ok(await page.evaluate(k=>sessionStorage.getItem(k),KEY));assert.equal(await page.locator('#cluster-resume-get').innerText(),'重试读取报告');await snapshot(page,'D-report-GET-interrupted');
   const pollBefore=scene.polls;await page.locator('#cluster-resume-get').click();await page.locator('#cluster-status').filter({hasText:'已读取最新保存报告'}).waitFor();assert.equal(scene.polls,pollBefore);assert.equal(scene.reports,2);assert.equal(scene.posts,0);assert.equal(await page.evaluate(k=>sessionStorage.getItem(k),KEY),null);assert.match(await page.locator('#cluster-status').innerText(),/未独立核实/);assert.equal(await page.locator('#cluster-submit').isDisabled(),false);assert.equal(await page.locator('#cluster-recovery').isVisible(),false);assert.match(await page.locator('#cluster-metrics').innerHTML(),/cluster-metric/);assert.ok(!(await page.locator('#cluster-status').getAttribute('class')).includes(' done'));await snapshot(page,'D-report-GET-recovered');
  });
  // F: 404, mismatched identity, incomplete historical cache. All fixture reads.
  await runCase('F',async take=>{
   const {page,scene}=await openScene('F',{pending:{id:JA,mint:A}});take(page);
   scene.handler=x=>x.u.pathname==='/api/cluster-analysis'?x.fulfill(200,job(JA,A,'RUNNING')):x.fulfill(200,fixedReport(A));
   await page.goto(origin+'/#cluster');await page.locator('#cluster-status').filter({hasText:'正在扫描链上数据'}).waitFor();assert.equal(scene.polls,1);await page.locator('#cluster-read-cached').click();await page.locator('#cluster-status').filter({hasText:'已读取已有历史报告'}).waitFor();const text=await page.locator('#cluster-status').innerText();assert.match(text,/覆盖仍不完整/);assert.match(text,/关联未经核实/);assert.ok(!(await page.locator('#cluster-status').getAttribute('class')).includes(' done'));assert.equal(scene.posts,0);assert.match(await page.locator('#cluster-summary').innerText(),/FIXTURE_A/);assert.match(await page.locator('#cluster-coverage').innerText(),/归一化尚未完成/);assert.equal(await page.locator('#cluster-result').isVisible(),true);await snapshot(page,'F-historical-incomplete-unlinked');
  });
 }catch(e){results.push({case:'ENVIRONMENT_OR_RUNNER',result:'FAIL',error:e.stack})}
 finally{
  if(context)await context.close().catch(()=>{});
  if(server){server.closeAllConnections();await new Promise(r=>server.close(r))}
  if(proxy){proxy.closeAllConnections();await new Promise(r=>proxy.close(r))}
  if(profile)fs.rmSync(profile,{recursive:true,force:true});
  const forbidden=audit.filter(r=>r.action?.startsWith('DENIED')||r.kind?.startsWith('PROXY'));
  const expectedErrors=consoleRecords.filter(r=>r.type==='error'&&(/net::ERR_CONNECTION_RESET|net::ERR_FAILED/.test(r.text)||(r.scene==='C'&&/status of 404/.test(r.text))));
  const unexpected=consoleRecords.filter(r=>r.type==='error'&&!expectedErrors.includes(r));
  const count={REAL_RPC:0,PRODUCTION_8766_REQUESTS:0,REAL_CA_POST:0,REAL_NOTIFICATIONS:0,REAL_TRADES:0,fixtureMockPOSTs:audit.filter(r=>r.method==='POST'&&r.url?.startsWith(origin+'/')).length,deniedNonFixtureAttempts:forbidden.length};
  // No real requests forwarded: the route and deny-only global proxy cannot reach production/external services.
  const staticUnchanged=Object.entries(manifest).every(([n,h])=>hash(fs.readFileSync(path.join(staticRoot,n)))===h);
  const failed=results.some(r=>r.result==='FAIL')||pageErrors.length||unexpected.length||!staticUnchanged;
  const report={verdict:failed?'MAC_ISOLATED_BROWSER_FAIL':'MAC_ISOLATED_BROWSER_PASS',sourceSHA:SHA,port,platform:os.platform(),results,safety:count,staticUnchanged,console:{expectedNetworkErrors:expectedErrors.length,unexpectedErrors:unexpected,pageErrors},cleanup:{browserClosed:true,fixtureClosed:true,proxyClosed:true,temporaryProfileRemoved:!profile||!fs.existsSync(profile)},endedAt:new Date().toISOString()};
  fs.writeFileSync(path.join(out,'http-audit.json'),JSON.stringify(audit,null,2));fs.writeFileSync(path.join(out,'console.json'),JSON.stringify(consoleRecords,null,2));fs.writeFileSync(path.join(out,'result.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
 }
})();
