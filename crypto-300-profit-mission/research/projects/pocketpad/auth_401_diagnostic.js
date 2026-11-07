/*
Pocket Pad 401 auth-path diagnostic. Chrome Console / Snippet, in the open pocketpad.io tab.
One-click, read-only account-access refresh. Never reads or prints credential values.
Does not create a voucher, sign, send ETH, or attempt to bypass Pocket authentication.
*/
(() => {
  "use strict";
  if (location.hostname !== "pocketpad.io" && location.hostname !== "www.pocketpad.io")
    throw new Error("Run this only on pocketpad.io");
  if (window.PocketAuth401?.installed)
    return console.info("PocketAuth401 already installed. Run await PocketAuth401.recheck()");

  const records = [];
  const watched = /^\/(?:me(?:\/|$)|mint\/pocket\/(?:state|eligibility|allowance|.*(?:voucher|pass|sign|auth)))/i;
  const allow = url => {
    try {
      const u = new URL(url, location.href);
      if (u.hostname !== "api.pocketpad.io" || !watched.test(u.pathname)) return null;
      return u.pathname;
    } catch (_) { return null; }
  };
  const save = (method,url,status,started,auth,credentials,kind) => {
    const path = allow(url);
    if (!path) return;
    const item = {
      path, method:String(method||"GET").toUpperCase(),
      status:status||"NETWORK_ERROR",
      authorizationHeader:!!auth,
      credentialsMode:credentials||"not specified",
      transport:kind,
      elapsedMs:Math.round(performance.now()-started)
    };
    records.push(item);
    if(records.length > 40) records.shift();
    console.info("[PocketAuth401]",item);
  };

  const originalFetch=window.fetch;
  window.fetch=function(input,init) {
    const url=typeof input==="string" ? input : input?.url || String(input);
    const method=init?.method || input?.method || "GET";
    const keys=new Set();
    try {
      new Headers(input instanceof Request ? input.headers : undefined)
        .forEach((v,k)=>keys.add(k.toLowerCase()));
      new Headers(init?.headers).forEach((v,k)=>keys.add(k.toLowerCase()));
    } catch (_) {}
    const start=performance.now();
    const creds=init?.credentials || input?.credentials || "default(same-origin)";
    const p=originalFetch.apply(this,arguments);
    p.then(res=>save(method,url,res.status,start,keys.has("authorization"),creds,"fetch"))
      .catch(()=>save(method,url,0,start,keys.has("authorization"),creds,"fetch"));
    return p;
  };

  const oldOpen=XMLHttpRequest.prototype.open;
  const oldHeader=XMLHttpRequest.prototype.setRequestHeader;
  const oldSend=XMLHttpRequest.prototype.send;
  XMLHttpRequest.prototype.open=function(method,url,...rest) {
    this.__pocket401={method,url,headers:new Set(),at:0};
    return oldOpen.call(this,method,url,...rest);
  };
  XMLHttpRequest.prototype.setRequestHeader=function(name,value) {
    if (this.__pocket401) this.__pocket401.headers.add(String(name).toLowerCase());
    return oldHeader.call(this,name,value);
  };
  XMLHttpRequest.prototype.send=function(...args) {
    const info=this.__pocket401;
    if (info) {
      info.at=performance.now();
      this.addEventListener("loadend",()=>{
        save(info.method,info.url,this.status,info.at,
          info.headers.has("authorization"),
          this.withCredentials?"include":"not include","xhr");
      },{once:true});
    }
    return oldSend.apply(this,args);
  };

  function report() {
    const recent=records.slice();
    console.table(recent);
    const unauth=recent.filter(x=>Number(x.status)===401);
    if (unauth.length)
      console.warn("401 confirmed: API rejected account access. A missing Authorization header or invalid/expired session are candidate causes; header presence alone does not prove validity.");
    else if (!recent.length)
      console.warn("No watched API calls captured. The app may use a different origin/path, or fetch was bound before instrumentation. Use Network -> Fetch/XHR and inspect request metadata without sharing tokens.");
    else
      console.info("No 401 seen in recorded requests; confirm UI result and /mint/pocket/allowance.");
    return recent;
  }
  async function recheck() {
    const button=[...document.querySelectorAll("button")].find(b=>/check access again/i.test(b.textContent||""));
    if (!button) {console.warn("No 'Check access again' button found. Click the official access-refresh control once manually, then call PocketAuth401.report().");return report();}
    console.info("Clicking the existing official Check access again button ONCE.");
    button.click();
    await new Promise(done=>setTimeout(done,2800));
    return report();
  }
  function restore() {
    window.fetch=originalFetch;
    XMLHttpRequest.prototype.open=oldOpen;
    XMLHttpRequest.prototype.setRequestHeader=oldHeader;
    XMLHttpRequest.prototype.send=oldSend;
    delete window.PocketAuth401;
    console.info("PocketAuth401 hooks removed.");
  }
  window.PocketAuth401=Object.freeze({installed:true,report,recheck,restore});
  console.info("Ready. Run: await PocketAuth401.recheck()");
})();
