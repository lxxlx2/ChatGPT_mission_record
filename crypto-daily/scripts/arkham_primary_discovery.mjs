import fs from 'node:fs';
import crypto from 'node:crypto';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const BASE = 'https://info.arkm.com';
const SURFACES = [BASE+'/research', BASE+'/sitemap.xml'];
const LIMIT = 32;
const nowISO = d => d.toISOString();
const digest = s => crypto.createHash('sha256').update(s).digest('hex').slice(0,24);
const clear = s => String(s || '').replace(/&amp;/g,'&').replace(/&quot;/g,'"').replace(/<[^>]+>/g,' ').replace(/\s+/g,' ').trim();

export function validArticle(url) {
  try {
    const u = new URL(url, BASE);
    if (u.origin !== BASE || !/^\/research\/[a-z0-9-]+\/?$/i.test(u.pathname)) return null;
    return BASE+u.pathname.replace(/\/$/,'');
  } catch { return null; }
}
export function extractArticleUrls(source) {
  const data = String(source||'').replaceAll('\\/','/');
  const result=[];
  for (const m of data.matchAll(/(?:https:\/\/info\.arkm\.com)?\/research\/[a-z0-9-]+\/?/gi)) {
    const u=validArticle(m[0]);
    if (u && !result.includes(u)) result.push(u);
  }
  return result;
}
export function parseArticle(url, source, checked = new Date()) {
  const target=validArticle(url);
  if (!target) throw new Error('UNTRUSTED_ARTICLE_URL');
  const html=String(source);
  const title=clear((html.match(/<h1[^>]*>([\s\S]*?)<\/h1>/i)||[,''])[1]);
  const text=clear(html);
  const meta=(html.match(/"datePublished"\s*:\s*"([^"]+)"/)||[,''])[1];
  const plainDate=(text.match(/(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+20\d{2}/i)||[])[0];
  const published=new Date(meta||plainDate||'');
  const dated=Number.isFinite(published.getTime());
  const fresh=dated && published.getTime()<=checked.getTime()+86400000 && published.getTime()>=checked.getTime()-96*3600000;
  const btc=/\bBTC\b|\bbitcoin\b/i.test(title+' '+text);
  const movement=/\btransfer(?:red|s)?\b|\bmoved\b|\bsent\b|\bdeposit\b|\bseiz(?:ed|ure)\b/i.test(title+' '+text);
  const amounts=[...text.matchAll(/([\d,]+(?:\.\d+)?)\s*BTC\b/gi)].map(m=>Number(m[1].replaceAll(',',''))).filter(Number.isFinite);
  const dollars=[...text.matchAll(/\$\s*([\d,.]+)\s*(million|billion|M|B)\b/gi)].map(m=>Number(m[1].replaceAll(',','')) * (/^b(?:illion)?$/i.test(m[2])?1e9:1e6));
  const txs=[...new Set([...html.matchAll(/(?:\/explorer\/tx\/)([a-fA-F0-9]{64})/g)].map(m=>m[1].toLowerCase()))];
  const version=txs.length?'tx:'+txs[0]:'source:'+digest(target);
  return {event_key:'arkham:'+version, family_key:'arkham:'+target.split('/').pop(), material_version:version,
    title, source_url:target, published_at:dated?nowISO(published):null, checked_at:nowISO(checked),
    btc, movement, fresh, btc_amounts:amounts.slice(0,8), usd_amounts:dollars.slice(0,8), txids:txs.slice(0,8),
    source_tier:'ARKHAM_ORIGINAL_ANALYTICS', priority:fresh&&btc&&movement&&(dollars.some(x=>x>=1e7)||amounts.some(x=>x>=100))?'HIGH_REVIEW':'NORMAL_REVIEW',
    qualification:'Arkham attribution is not independent proof of beneficial ownership, law enforcement seizure or spot sale.'};
}
export function orderedUrls(surfaces) {
  const ranked=[];
  for(const s of surfaces) if(!s.error){
    for(const entry of String(s.body||'').matchAll(/<url>([\s\S]*?)<\/url>/gi)){
      const loc=(entry[1].match(/<loc>([^<]+)<\/loc>/i)||[])[1];
      const last=(entry[1].match(/<lastmod>([^<]+)<\/lastmod>/i)||[])[1];
      const u=validArticle(loc);
      if(u)ranked.push({url:u,timestamp:Date.parse(last||'')||0});
    }
    for(const u of extractArticleUrls(s.body))ranked.push({url:u,timestamp:s.url==='manual-seed'?Number.MAX_SAFE_INTEGER:0});
  }
  ranked.sort((a,b)=>b.timestamp-a.timestamp);
  return [...new Set(ranked.map(x=>x.url))];
}
export function scanOffline(surfaces, articles, now = new Date()) {
  const source_receipts=surfaces.map(s=>({url:s.url,status:s.error?'SOURCE_GAP':'CHECKED',checked_at:nowISO(now),error:s.error||null}));
  const urls=orderedUrls(surfaces);
  const candidates=[],article_gaps=[];
  for(const u of urls.slice(0,LIMIT)){
    if(!articles[u]||articles[u].error){article_gaps.push({url:u,reason:articles[u]?.error||'ARTICLE_NOT_READ'});continue}
    const c=parseArticle(u,articles[u].body,now);
    if(c.fresh&&c.btc&&c.movement)candidates.push(c);
  }
  const seen=new Set();
  const unique=candidates.filter(c=>{if(seen.has(c.event_key))return false;seen.add(c.event_key);return true});
  return {checked_at:nowISO(now),source_receipts,article_gaps,article_links_found:urls.length,article_read_limit:LIMIT,
    candidates:unique,candidate_count:unique.length,status:source_receipts.every(x=>x.status==='CHECKED')&&!article_gaps.length?'INDEX_SOURCE_CHECKED':'PARTIAL_SOURCE_GAP',
    caveat:'Index checked is not full on-chain coverage. A transfer not published by Arkham can still be missed. Validate tx and labels independently before publication.'};
}
async function get(url){
  const u=new URL(url);
  if(u.protocol!=='https:'||u.hostname!=='info.arkm.com')throw new Error('NOT_ALLOWED_ORIGIN');
  const res=await fetch(url,{redirect:'manual',signal:AbortSignal.timeout(10000)});
  if(!res.ok||res.status>=300)throw new Error('HTTP_'+res.status);
  if(Number(res.headers.get('content-length')||0)>2000000)throw new Error('BODY_TOO_LARGE');
  const body=await res.text();
  if(body.length>2000000)throw new Error('BODY_TOO_LARGE');
  return body;
}
export async function scanLive(when=new Date(),seedUrl=null){
  const surfaces=await Promise.all(SURFACES.map(async url=>{try{return {url,body:await get(url)}}catch(e){return {url,error:String(e?.message||e)}}}));
  const urls=orderedUrls(surfaces);
  if(seedUrl){const u=validArticle(seedUrl);if(!u)throw new Error('INVALID_SEED_URL');urls.unshift(u)}
  const articles={};
  for(const u of [...new Set(urls)].slice(0,LIMIT)){
    try{articles[u]={body:await get(u)}}catch(e){articles[u]={error:String(e?.message||e)}}
  }
  const scan=scanOffline([...(seedUrl?[{url:'manual-seed',body:validArticle(seedUrl)}]:[]),...surfaces],articles,when);
  return scan;
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
  const fixture=process.argv.indexOf('--offline-json'),seed=process.argv.indexOf('--seed-url'),at=process.argv.indexOf('--as-of');
  const time=at>=0?new Date(process.argv[at+1]):new Date();
  if(!Number.isFinite(time.getTime()))throw new Error('INVALID_AS_OF');
  const r=fixture>=0?scanOffline(...(function(){const x=JSON.parse(fs.readFileSync(process.argv[fixture+1],'utf8'));return [x.surfaces,x.articles,time]})()):await scanLive(time,seed>=0?process.argv[seed+1]:null);
  process.stdout.write(JSON.stringify(r,null,2)+'\n');
  if(r.status!=='INDEX_SOURCE_CHECKED')process.exitCode=2;
}
