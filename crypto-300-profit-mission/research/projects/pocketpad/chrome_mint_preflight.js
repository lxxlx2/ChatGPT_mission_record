/*
Pocket Pad public-mint preflight, Chrome DevTools Snippet.
Local-only. No private keys, cookies, OTPs, tokens or signatures are printed or uploaded.
No automatic sending. Minting requires explicit PocketMint.send(tx) and wallet approval.
Source and limitations: see README.md beside this file.
*/
(() => {
  "use strict";
  if (location.protocol !== "https:" || !["pocketpad.io", "www.pocketpad.io"].includes(location.hostname)) {
    throw new Error("Only run inside the authenticated https://pocketpad.io/ tab");
  }
  if (window.PocketMint?.installed) return console.info("PocketMint already installed; refresh to reinstall.");
  const CONTRACT = "0x3a98DE41A0dF554F6b69Ca1b5A1Ad93a745AB1F2";
  const CHAIN = "0x1237";
  const RPC = "https://rpc.mainnet.chain.robinhood.com";
  const SELECTOR = "0x98dd0156";
  const ONE = 30000000000000000n;
  const observed = [];
  let voucher = null;
  const nativeFetch = window.fetch;
  const isHex = x => typeof x === "string" && /^0x[0-9a-fA-F]*$/.test(x);
  const w = x => { const n=BigInt(x); if(n<0n || n>=2n**256n) throw Error("uint256 out of range"); return n.toString(16).padStart(64,"0"); };
  const safePath = path => path.split("/").map(x =>
    x.includes("@") || /^0x[0-9a-f]{30,}$/i.test(x) || /^[0-9a-f]{28,}$/i.test(x) ? ":redacted" : x).join("/");
  const observeURL = (url, method, status, elapsed) => {
    try {
      const u = new URL(url, location.href);
      if (!/(^|\.)pocketpad\.io$/.test(u.hostname) || !/access|eligib|check|mint|phase|voucher|pass|signature|wallet/i.test(u.pathname)) return;
      const entry = {path:safePath(u.pathname), method:String(method), status, ms:Math.round(elapsed), at:new Date().toLocaleTimeString()};
      observed.push(entry); if(observed.length>80) observed.shift();
      console.info("[PocketMint request]", entry);
    } catch (_) {}
  };
  function detect(obj, depth=0) {
    if (!obj || typeof obj!=="object" || depth>6) return;
    if (isHex(obj.signature) && /^0x[0-9a-fA-F]{130}$/.test(obj.signature)
       && /^0x[0-9a-fA-F]{64}$/.test(obj.identityHash || "")
       && obj.nonce!==undefined && obj.deadline!==undefined && obj.quantity!==undefined) {
      voucher = {
        identityHash: obj.identityHash, quantity:String(obj.quantity),
        nonce:String(obj.nonce), deadline:String(obj.deadline), signature:obj.signature
      };
      console.info("[PocketMint] Voucher captured in THIS tab; signature hidden; quantity:",
        voucher.quantity, "expiry:",new Date(Number(BigInt(voucher.deadline))*1000).toLocaleString());
      return;
    }
    for (const x of Object.values(obj)) if(x && typeof x==="object") detect(x,depth+1);
  }
  function inspectResponse(url,response) {
    try {
      const u = new URL(url, location.href);
      if (!/(^|\.)pocketpad\.io$/.test(u.hostname) || !/access|eligib|check|mint|voucher|signature/i.test(u.pathname)) return;
      if (!response.headers.get("content-type")?.includes("json")) return;
      if (Number(response.headers.get("content-length")||0)>250000) return;
      response.clone().json().then(x=>detect(x)).catch(()=>{});
    } catch (_) {}
  }
  window.fetch = function (...args) {
    const input=args[0], url=typeof input==="string" ? input : input?.url ?? String(input);
    const method=args[1]?.method ?? input?.method ?? "GET", start=performance.now();
    const promise=nativeFetch.apply(this,args);
    promise.then(res=>{
      observeURL(url,method,res.status,performance.now()-start);
      inspectResponse(url,res);
    }).catch(()=>observeURL(url,method,"NETWORK_ERROR",performance.now()-start));
    return promise;
  };
  const xhrOpen=XMLHttpRequest.prototype.open, xhrSend=XMLHttpRequest.prototype.send;
  XMLHttpRequest.prototype.open = function (method,url,...args) {
    this.__pocketMeta={method,url};
    return xhrOpen.call(this,method,url,...args);
  };
  XMLHttpRequest.prototype.send = function (...args) {
    const meta=this.__pocketMeta, start=performance.now();
    if(meta) this.addEventListener("loadend",()=>{
      observeURL(meta.url,meta.method,this.status||"NETWORK_ERROR",performance.now()-start);
      try {
        const u=new URL(meta.url,location.href);
        if (/(^|\.)pocketpad\.io$/.test(u.hostname)
           && /access|eligib|check|mint|voucher|signature/i.test(u.pathname)
           && this.getResponseHeader("content-type")?.includes("json")) {
          if (this.responseType==="json") detect(this.response);
          else if (this.responseType==="" || this.responseType==="text") detect(JSON.parse(this.responseText));
        }
      } catch (_) {}
    },{once:true});
    return xhrSend.apply(this,args);
  };
  async function rpc(method,params) {
    try {
      const res=await nativeFetch.call(window,RPC,{
        method:"POST",headers:{"content-type":"application/json"},
        body:JSON.stringify({jsonrpc:"2.0",id:1,method,params})
      });
      if(!res.ok) throw Error("RPC HTTP "+res.status);
      const j=await res.json();
      if(j.error) throw Error(j.error.message||JSON.stringify(j.error));
      return j.result;
    } catch (err) {
      const injected=window.ethereum;
      if(!injected?.request) throw Error("RPC request blocked/failed; open Network for details: "+err.message);
      const chain=await injected.request({method:"eth_chainId"});
      if(chain?.toLowerCase()!==CHAIN) throw Error("RPC failed and injected wallet not on Robinhood Chain");
      return injected.request({method,params});
    }
  }
  async function snapshot() {
    const calls=[
      ["phase","0x17881cbf"],["totalMinted","0xa2309ff8"],
      ["allowlistMinted","0x32d6f032"],["reserveMinted","0x4c81433f"],
      ["paused","0x5c975abb"],["finalSupply","0x2baabbf7"]
    ];
    const block=await rpc("eth_blockNumber",[]);
    const items=await Promise.all(calls.map(async ([name,data])=>
      [name,Number(BigInt(await rpc("eth_call",[{to:CONTRACT,data},block])))]));
    const result={block:Number(BigInt(block)),chainId:await rpc("eth_chainId",[]),...Object.fromEntries(items)};
    result.publicFunctionMints=result.totalMinted-result.allowlistMinted-result.reserveMinted;
    console.table(result);
    if(result.phase===1) console.warn("phase=1: allowlist stage. Public-function mints may be allowlisted users' second mints.");
    return result;
  }
  async function scanScripts() {
    const assets=[...new Set([...document.scripts].map(s=>s.src).filter(Boolean))]
      .filter(x=>new URL(x).origin===location.origin).slice(0,35);
    const result=[];
    for(const url of assets) {
      try {
        const res=await nativeFetch.call(window,url,{credentials:"omit"});
        if(!res.ok || Number(res.headers.get("content-length")||0)>3500000) continue;
        const source=await res.text();
        const found=["mintPublic","mintAllowlist","identityHash","voucher","checkAccess","allowlist","/api/"]
          .filter(k=>source.includes(k));
        if(found.length) result.push({asset:new URL(url).pathname,keywords:found.join(", ")});
      } catch (_) {}
    }
    console.table(result);
    return result;
  }
  function status() {
    const detail={installed:true,contract:CONTRACT,chainId:CHAIN,
      requests:observed.slice(),hasVoucher:!!voucher,
      voucherQuantity:voucher?.quantity||null,
      voucherExpiry:voucher?new Date(Number(BigInt(voucher.deadline))*1000).toISOString():null};
    console.info("[PocketMint diagnostics; no secrets]",detail);
    return detail;
  }
  function prepare(from) {
    if(!voucher) throw Error("No valid voucher captured. Use the site's legitimate mint/eligibility flow.");
    if(!/^0x[0-9a-fA-F]{40}$/.test(from||"")) throw Error("Supply exact eligible Privy wallet address.");
    const qty=BigInt(voucher.quantity), expires=BigInt(voucher.deadline);
    if(qty<1n || qty>2n) throw Error("Unsupported quantity");
    if(expires<=BigInt(Math.floor(Date.now()/1000))) throw Error("Voucher expired; request a fresh one");
    const signature=voucher.signature.slice(2), len=signature.length/2;
    const data=SELECTOR+voucher.identityHash.slice(2)+w(qty)+w(voucher.nonce)+w(expires)+w(160)+w(len)
      +signature.padEnd(Math.ceil(signature.length/64)*64,"0");
    const tx={from,to:CONTRACT,chainId:CHAIN,value:"0x"+(qty*ONE).toString(16),data};
    console.warn("Unsigned tx prepared locally. Do not post calldata/voucher publicly. No transaction sent.");
    return tx;
  }
  async function simulate(tx) {
    validate(tx);
    const result=await rpc("eth_call",[{from:tx.from,to:tx.to,value:tx.value,data:tx.data},"latest"]);
    console.info("[PocketMint] eth_call accepted; this DOES NOT guarantee a successful future transaction.",result);
    return result;
  }
  function validate(tx) {
    if(!tx || tx.to?.toLowerCase()!==CONTRACT.toLowerCase() || tx.chainId!==CHAIN
      || !/^0x98dd0156[0-9a-fA-F]+$/.test(tx.data||"")
      || !/^0x[0-9a-fA-F]{40}$/.test(tx.from||"")) throw Error("Invalid transaction/chain/address");
    if(![ONE,ONE*2n].includes(BigInt(tx.value))) throw Error("Unexpected payment amount");
  }
  async function send(tx) {
    validate(tx);
    const provider=window.ethereum;
    if(!provider?.request) throw Error("No injected EIP-1193 wallet. Privy embedded wallet may require its own SDK; never export keys.");
    const chain=await provider.request({method:"eth_chainId"});
    if(chain?.toLowerCase()!==CHAIN) throw Error("Injected wallet is not on Robinhood Chain");
    const accounts=await provider.request({method:"eth_accounts"});
    if(!accounts?.some(x=>x.toLowerCase()===tx.from.toLowerCase())) throw Error("Injected wallet does not match signed recipient");
    await simulate(tx);
    console.warn("Next operation requests real wallet confirmation and can spend ETH; approve only if intended.");
    return provider.request({method:"eth_sendTransaction",params:[{
      from:tx.from,to:tx.to,value:tx.value,data:tx.data
    }]});
  }
  window.PocketMint=Object.freeze({installed:true,contract:CONTRACT,status,snapshot,scanScripts,
    hasVoucher:()=>!!voucher,prepare,simulate,send});
  console.info("[PocketMint] Installed. Click 'Check access again'; run PocketMint.status(), await PocketMint.snapshot().");
  console.info("Only if the official service delivers a valid voucher: const tx=PocketMint.prepare('0xYOUR_PRIVY_WALLET')");
})();
