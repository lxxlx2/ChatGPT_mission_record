// Actual Chrome acceptance, localhost and synthetic data only. Explicitly opt-in.
const assert = require('node:assert/strict');
const {spawn} = require('node:child_process');
const {mkdtempSync, rmSync} = require('node:fs');
const {tmpdir} = require('node:os');
const {join} = require('node:path');
const {once} = require('node:events');
const readline = require('node:readline');
const {chromium} = require(process.env.FRANK_PLAYWRIGHT_MODULE || 'playwright');

async function run() {
  const profile = mkdtempSync(join(tmpdir(), 'frank-parallel-ca-chrome-'));
  const child = spawn(process.env.FRANK_PYTHON || 'python3',
    ['-I', '-B', join(__dirname, 'fixtures/frank_parallel_ca_browser_server.py')],
    {env:{PATH:process.env.PATH, LANG:'en_US.UTF-8'}, stdio:['pipe','pipe','inherit']});
  child.stdin.on('error', ()=>{});
  const done = once(child, 'exit');
  const lines = readline.createInterface({input:child.stdout});
  const watchdog = setTimeout(()=>child.kill('SIGTERM'), 70000);
  let context;
  try {
    const [line] = await Promise.race([once(lines, 'line'), done.then(()=>{throw Error('fixture exited before ready');})]);
    const config = JSON.parse(line), {port, mint_a, mint_b, owner, pool_b} = config;
    assert.ok(port && ![8765,8766].includes(port));
    const origin = 'http://127.0.0.1:'+port;
    const read = async path=>{
      const response = await fetch(origin+path);
      assert.equal(response.status, 200);
      return response.json();
    };
    const denied = [], pages = [], requests = [];
    context = await chromium.launchPersistentContext(profile, {
      executablePath:process.env.FRANK_CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
      headless:true, serviceWorkers:'block',
      args:['--disable-background-networking','--disable-component-update','--disable-sync','--no-first-run',
        '--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1']
    });
    await context.route('**/*', route=>{
      const request=route.request(), url=new URL(request.url()), method=request.method();
      if (url.origin!==origin || !['GET','POST'].includes(method) ||
          (method==='POST' && url.pathname!=='/api/cluster-analysis')) {
        denied.push(method+':outside fixture');
        return route.abort();
      }
      requests.push({method,path:url.pathname,query:url.search});
      return route.continue();
    });
    async function pageFor(mint) {
      const page = await context.newPage();
      page.setDefaultTimeout(10000);
      page.on('pageerror', error=>pages.push(error.message));
      await page.goto(origin+'/#cluster');
      await page.locator('#cluster-submit').waitFor({state:'visible'});
      await page.locator('#cluster-mint').fill(mint);
      return page;
    }
    async function submit(page, locator, expectation) {
      const pending=page.waitForResponse(response=>response.url()===origin+'/api/cluster-analysis' &&
        response.request().method()==='POST');
      await locator.click();
      const response=await pending;
      assert.equal(response.status(),202);
      const job=await response.json();
      for(const [key,value] of Object.entries(expectation)) assert.equal(job[key],value);
      return job;
    }
    const first=await pageFor(mint_a);
    const second=await pageFor(mint_b);
    const overviewA=await submit(first,first.locator('#cluster-submit'),{mint:mint_a,query_scope:'overview'});
    await first.locator('#cluster-full-query').waitFor({state:'visible'});
    await first.locator('#cluster-series-chart').getByText('本次访问来源',{exact:false}).waitFor();
    const full=await submit(first,first.locator('#cluster-full-query'),
      {mint:mint_a,query_scope:'full',base_job_id:overviewA.job_id});
    const jobPath=id=>'/api/cluster-analysis?job_id='+id;
    const overviewB=await submit(second,second.locator('#cluster-submit'),{mint:mint_b,query_scope:'overview'});
    await second.locator('#cluster-full-query').waitFor({state:'visible'});
    assert.equal((await read(jobPath(full.job_id))).status,'RUNNING');
    assert.equal((await read(jobPath(overviewB.job_id))).status,'DONE');
    await second.locator('#cluster-series-chart').getByText('本次访问来源',{exact:false}).waitFor();
    const countsBefore=await read('/__fixture/counts');
    assert.ok(countsBefore.chart>=2 && countsBefore.trades>=2);
    await read('/__fixture/throttle');
    const refreshResponse=second.waitForResponse(response=>{
      const url=new URL(response.url());
      return url.origin===origin && url.pathname==='/api/cluster-market-series' && url.searchParams.get('refresh')==='1';
    });
    await second.locator('#cluster-series-load').click();
    const market=await (await refreshResponse).json();
    assert.equal(market.job_id,overviewB.job_id);
    assert.equal(market.pool,pool_b);
    assert.equal(market.chart.reason,'HTTP_429');
    assert.equal(market.trades.source_attempted,false);
    await second.locator('#cluster-series-chart').getByText('显示上次数据',{exact:false}).waitFor();
    await second.locator('#cluster-series-trades').getByText('本次未访问来源',{exact:false}).waitFor();
    const countsAfter=await read('/__fixture/counts');
    assert.equal(countsAfter.chart,countsBefore.chart+1);
    assert.equal(countsAfter.trades,countsBefore.trades);

    const ownerButton=second.locator('button[data-cluster-owner="'+owner+'"]').first();
    if (!(await ownerButton.isVisible())) await second.locator('#cluster-holder-title').click();
    const wallet=await submit(second,ownerButton,
      {mint:mint_b,query_scope:'wallet',focus_owner:owner,base_job_id:overviewB.job_id});
    await second.locator('#cluster-wallet-detail').getByText('此明细仅核对选中的 Owner 和这个 CA。').waitFor({state:'attached'});
    assert.equal((await read(jobPath(wallet.job_id))).status,'DONE');
    assert.equal((await read(jobPath(full.job_id))).status,'RUNNING');
    const report=await read('/api/cluster-latest?mint='+mint_b+'&job_id='+wallet.job_id);
    assert.equal(report.base_job_id,overviewB.job_id);
    const crossed=await fetch(origin+'/api/cluster-latest?mint='+mint_a+'&job_id='+overviewB.job_id);
    assert.equal(crossed.status,404);
    assert.equal(requests.filter(request=>request.method==='POST').length,4);
    assert.deepEqual(denied,[]);
    assert.deepEqual(pages,[]);
    await read('/__fixture/release');
    console.log('PASS: Chrome isolated overview and wallet while full is running; source-refresh throttle and scoped report readback');
  } finally {
    try { if(context) await context.close(); }
    finally {
      child.stdin.end();
      await done;
      clearTimeout(watchdog);
      lines.close();
      rmSync(profile,{recursive:true,force:true});
    }
  }
}
run().catch(error=>{ console.error(error);process.exitCode=1; });
