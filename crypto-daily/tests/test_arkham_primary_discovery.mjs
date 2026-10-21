import test from 'node:test';
import assert from 'node:assert/strict';
import { validArticle, extractArticleUrls, parseArticle, orderedUrls, scanOffline } from '../scripts/arkham_primary_discovery.mjs';

const now=new Date('2026-10-21T02:00:00Z');
const a='https://info.arkm.com/research/clifton-collins-fifth-500-btc-40m-transfer-from-drug-dealers-lost-stack';
const b='https://info.arkm.com/research/another-500-btc-transfer';
const hash='eb0bde50049e924590a1812af2d2699c13d513415d3f03bbe3d10f316b3d6756';
const html='<html><script type="application/ld+json">{"datePublished":"2026-10-20T17:25:00Z"}</script><h1>Clifton Collins fifth 500 BTC transfer</h1><p>Transferred 500 BTC worth $41.5 million to Coinbase Prime.</p><a href="https://arkm.com/explorer/tx/'+hash+'">TXID</a></html>';
const other='<html><script>{"datePublished":"2026-10-20T18:00:00Z"}</script><h1>Another wallet transferred 500 BTC</h1><p>Transferred 500 BTC worth $43 million.</p></html>';
const index='<a href="'+a+'">a</a><a href="'+b+'">b</a>';

test('recognizes actual Oct20 Arkham 500 BTC as material new primary candidate',()=>{
 const c=parseArticle(a,html,now);
 assert.equal(c.priority,'HIGH_REVIEW');
 assert.equal(c.fresh,true);
 assert.equal(c.btc,true);
 assert.equal(c.movement,true);
 assert.ok(c.usd_amounts.includes(41500000));
});
test('captures transaction identity instead of only quantity',()=>assert.ok(parseArticle(a,html,now).txids.includes(hash)));
test('rejects untrusted URL and open redirects',()=>assert.equal(validArticle('https://not-arkm.example/research/clifton-collins'),null));
test('extracts the article URLs from first-party index',()=>assert.deepEqual(extractArticleUrls(index),[a,b]));
test('does not collapse two fresh 500 BTC stories by amount',()=>{
 const r=scanOffline([{url:'index',body:index}],{[a]:{body:html},[b]:{body:other}},now);
 assert.equal(r.candidate_count,2);
 assert.notEqual(r.candidates[0].event_key,r.candidates[1].event_key);
});
test('unreadable article is PARTIAL, never falsely marked successful',()=>{
 const r=scanOffline([{url:'index',body:index}],{[a]:{body:html}},now);
 assert.equal(r.status,'PARTIAL_SOURCE_GAP');
 assert.equal(r.article_gaps.length,1);
});
test('source 403 is a source gap with a receipt',()=>{
 const r=scanOffline([{url:'index',error:'HTTP_403'}],{},now);
 assert.equal(r.status,'PARTIAL_SOURCE_GAP');
 assert.equal(r.source_receipts[0].status,'SOURCE_GAP');
});
test('new sitemap lastmod is prioritized over old article',()=>{
 const sitemap='<url><loc>'+b+'</loc><lastmod>2026-07-01</lastmod></url><url><loc>'+a+'</loc><lastmod>2026-10-20</lastmod></url>';
 assert.equal(orderedUrls([{url:'sitemap',body:sitemap}])[0],a);
});
test('explicit seed still stays first even with many dated sitemap links',()=>{
 const sources=[{url:'manual-seed',body:a},{url:'sitemap',body:'<url><loc>'+b+'</loc><lastmod>2026-10-20</lastmod></url>'}];
 assert.equal(orderedUrls(sources)[0],a);
});
test('stale incident cannot pass 96-hour freshness window',()=>assert.equal(parseArticle(a,html,new Date('2026-11-11T00:00:00Z')).fresh,false));
test('malformed article date is not accepted as fresh',()=>{
 const c=parseArticle(a,'<h1>500 BTC moved</h1><p>Transferred 500 BTC</p>',now);
 assert.equal(c.fresh,false);
 assert.equal(c.published_at,null);
});
test('other origin articles are not copied into primary source evidence',()=>assert.deepEqual(extractArticleUrls('<a href="https://fake.example/research/fake">test</a>'),[]));
