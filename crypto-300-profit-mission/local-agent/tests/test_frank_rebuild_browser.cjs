// Actual Chrome, shipped static assets, synthetic same-origin GET responses.
// No external requests, POSTs, listening port, production files, or active profile.
const assert = require('node:assert/strict');
const { chromium } = require(process.env.FRANK_PLAYWRIGHT_MODULE || 'playwright');
const { readFile } = require('node:fs/promises');
const { join } = require('node:path');

const origin = 'http://127.0.0.254:8766';
const assetRoot = join(__dirname, '../mission_agent/mission_control/static');
const a = '1'.repeat(31)+'2', b = '1'.repeat(31)+'3';
const pool = '1'.repeat(31)+'4', peer = '1'.repeat(31)+'5', alternate = '1'.repeat(31)+'6';
const jobs = {[a]:'a'.repeat(32),[b]:'b'.repeat(32)};
const t = 1792683600, older = t-300;
const report = mint => ({mint, ca_job_id:jobs[mint], observed_at:t, query_scope:'overview',
  coverage:{}, metrics:{}, assessment:{}, holders:[], limitations:[], transaction_errors:[],
  token_profile:{status:'OK',is_initialized:true},
  market:{status:'OK',chain:'solana',mint,name:mint===a?'合成样本甲':'合成样本乙',
    main_pair:{pair_address:pool,base_address:mint,quote_address:peer},
    pool_candidates:[{pair_address:alternate,base_address:mint,quote_address:peer}]}});
const series = (mint,selectedPool,period,before) => {
  const stamp=before===t?older:before===older?null:t;
  const p=stamp===t?(mint===a?'7':'11'):'3';
  return {mint,job_id:jobs[mint],pool:selectedPool,period,before:before||undefined,
    source:'GECKOTERMINAL_PUBLIC_API',currency:'USD',
    chart:{status:'OK',observed_at:t,rows:stamp?[[stamp,p,p,p,p,'5']]:[],
      coverage:{before:before||null,next_before:stamp}},
    ...(before?{}:{trades:{status:'OK',observed_at:t,coverage:{},rows:[
      {wallet:peer,side:'BUY',quantity:mint===a?'42':'71',at:t,signature:'1'.repeat(64)}
    ]}})};
};
const buy = {mint:a,name:'已核实样例',signature:'1'.repeat(64),at:t,
  quantity:'1234567.12345',paid:'0.00000001',currency:'USDC',spent_usd:'120.125',entry_price_usd:'0.0000001234'};
const unpriced = {mint:b,name:'无美元价格样例',signature:'2'.repeat(64),at:t-10,quantity:'700',paid:'2',currency:'SOL'};

const estimated = {mint:a,name:'同秒换算样例',signature:'3'.repeat(64),at:t-15,
  spent_usd:null,entry_price_usd:null,estimated_spent_usd:'0.4935',estimated_entry_price_usd:'0.24675',
  usd_estimate_basis:'PAYMENT_ASSET_MARKET_TRADE_SAME_SECOND'};

(async () => {
  const chrome = await chromium.launch({executablePath: process.env.FRANK_CHROME ||
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    args:['--disable-background-networking','--disable-sync','--host-resolver-rules=MAP * ~NOTFOUND']});
  try {
    const page = await chrome.newPage({viewport:{width:1390,height:930}});
    const errors=[], forbidden=[], marketRequests=[], apiRequests=[];
    page.on('pageerror', error=>errors.push(String(error)));
    await page.addInitScript(seed=>{
      localStorage.setItem('mission-meme-cluster-reports-v1',JSON.stringify(seed));
    },[a,b].map(mint=>({id:jobs[mint],mint,observed_at:t,scope:'overview'})));
    await page.route('**/*', async route => {
      const req=route.request(), u=new URL(req.url()), path=u.pathname;
      if (u.origin!==origin || req.method()!=='GET') {
        forbidden.push([req.method(),u.origin,path]); return route.abort();
      }
      const json=data=>route.fulfill({json:data});
      if (path.startsWith('/api/')) apiRequests.push(path);
      if (path==='/api/frank-buys') {
        return json({status:'LOCAL_EVIDENCE_ONLY',next_cursor:null,rows:u.searchParams.has('mint')?[]:[buy,unpriced,estimated]});
      }
      if (path==='/api/cluster-latest') {
        const mint=u.searchParams.get('mint');
        return json(u.searchParams.get('job_id')===jobs[mint] && jobs[mint] ? report(mint):null);
      }
      if (path==='/api/cluster-market-series') {
        const mint=u.searchParams.get('mint'), before=Number(u.searchParams.get('before'));
        const selectedPool=u.searchParams.get('pool'), period=u.searchParams.get('period');
        marketRequests.push({mint,before,pool:selectedPool,period});
        return json(series(mint,selectedPool,period,before));
      }
      if (path==='/' || /^\/static\/[\w.-]+$/.test(path)) {
        const type=path==='/'?'text/html':path.endsWith('.js')?'application/javascript':path.endsWith('.css')?'text/css':'text/plain';
        return route.fulfill({contentType:type,body:await readFile(join(assetRoot,path==='/'?'index.html':path.split('/').at(-1)))});
      }
      return route.fulfill({status:404,body:''});
    });
    const waitText = (selector, text, exact=false) => page.waitForFunction(([selector,text,exact]) =>
      [...document.querySelectorAll(selector)].some(el=>exact?el.textContent.trim()===text:el.textContent.includes(text)),
      [selector,text,exact],{timeout:6000});

    await page.goto(origin+'/',{waitUntil:'domcontentloaded'});
    await waitText('#frank-buy-rows','$120.13');
    await waitText('#frank-buy-rows','$1.23E-7');
    const buyText=await page.locator('#buys-view').innerText();
    assert.match(buyText,/已核实样例/);
    assert.doesNotMatch(buyText,/仅展示|证据齐全|枚数|USDC|SOL\b|滑点|路由|来源信号/);
    assert.equal(await page.getByRole('row',{name:/无美元价格样例/}).locator('.buy-value').filter({hasText:/—/}).count(),2);
    const estimates=page.getByRole('row',{name:/同秒换算样例/}).locator('.buy-usd-estimate');
    assert.deepEqual(await estimates.allTextContents(),['≈$0.49','≈$0.25']);
    assert.match(await estimates.first().getAttribute('title'),/并非美元实付/);
    assert.deepEqual(apiRequests,['/api/frank-buys']);
    assert.deepEqual(await page.locator('.view-tab').allTextContents(),['买入记录','CA 查询']);
    await page.keyboard.press('Tab');
    assert.equal(await page.evaluate(()=>document.activeElement.matches(':focus-visible')),true);
    await page.locator('#frank-buy-rows').getByRole('button',{name:'查 CA'}).first().click();
    assert.equal(await page.locator('#cluster-mint').inputValue(),a);
    assert.equal(await page.locator('h1').innerText(),'Meme 研究台');
    const choose=async mint=>{
      const history=page.locator('.workspace-history');
      if (!await history.evaluate(el=>el.open)) await history.locator('summary').click();
      await page.locator('#cluster-reports').selectOption(jobs[mint]);
      await page.locator('#cluster-read-report').click();
      await page.locator('#cluster-series-panel').waitFor({state:'visible',timeout:6000});
      assert.equal(await page.locator('#cluster-mint').inputValue(),mint);
    };
    await choose(a);
    await waitText('#cluster-series-chart td','7',true);
    await waitText('#cluster-series-trades td','42',true);
    await page.locator('#cluster-series-older').click();
    await waitText('#cluster-series-chart td','3',true);
    await waitText('#cluster-series-trades td','42',true);
    await page.locator('#cluster-series-older').click();
    await waitText('#cluster-series-status','来源未返回更早');
    assert(await page.locator('#cluster-series-older').isDisabled());
    await page.locator('#cluster-series-newer').click();
    await waitText('#cluster-series-chart td','7',true);
    await page.locator('#cluster-series-period').selectOption('1h');
    await page.waitForFunction(()=>document.querySelector('#cluster-series-chart svg'));
    await page.locator('#cluster-series-pool').selectOption(alternate);
    await page.waitForFunction(()=>document.querySelector('#cluster-series-chart svg'));
    assert(marketRequests.some(row=>row.pool===alternate && row.period==='1h' && row.before===0));
    await choose(b);
    await waitText('#cluster-series-trades td','71',true);
    assert(!((await page.locator('#cluster-series-trades').textContent()).includes('42')));
    await choose(a);
    await waitText('#cluster-series-trades td','42',true);
    assert(marketRequests.some(row=>row.mint===a && row.before===t));
    assert(marketRequests.some(row=>row.mint===a && row.before===older));
    assert(marketRequests.some(row=>row.mint===b && row.before===0));
    for (const width of [390,320]) {
      await page.setViewportSize({width,height:844});
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
      await page.getByRole('button',{name:'买入记录'}).click();
      await waitText('#frank-buy-rows','$120.13');
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
      await page.getByRole('button',{name:'CA 查询'}).click();
    }
    assert.deepEqual(forbidden,[]);
    assert.deepEqual(errors,[]);
    console.log(JSON.stringify({chrome:chrome.version(),evidence:'synthetic browser requests intercepted, no TCP listener',
      unique_ca:2,frank_default:'PASS',usd_estimate_label:'PASS',chart_next_previous_exhaustion:'PASS',A_B_A:'PASS',market_GET:marketRequests.length,mobile_320_390:'PASS',keyboard_focus:'PASS',external_or_POST:0,page_errors:0}));
  } finally { await chrome.close(); }
})().catch(error=>{console.error(error);process.exitCode=1;});
