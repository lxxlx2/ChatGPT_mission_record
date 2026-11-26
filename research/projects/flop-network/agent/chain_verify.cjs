// Read-only independent verification against the official finalized Testnet.
// JSON input contains only public chain identifiers. No signing or secrets.
const fs = require('node:fs');
const { createRequire } = require('node:module');
const PIN = '0x918abd58fb16306b30ef3886514cfaebffecb4de43e82b6f8ec4795c43cfd800';
const HASH = /^0x[0-9a-f]{64}$/i;
const norm = s => String(s).replace(/[^a-z0-9]/gi,'').toLowerCase();
const deadline = setTimeout(()=>process.exit(3),45000);
async function main(){
  const q=JSON.parse(fs.readFileSync(0,'utf8'));
  if(q.genesis!==PIN)throw Error('GENESIS_PIN');
  const req=createRequire(fs.realpathSync(q.cli));
  let lib;try{lib=req('@polkadot/api');}catch{lib=createRequire(req.resolve('@flop-labs/sdk'))('@polkadot/api');}
  const {ApiPromise,HttpProvider}=lib;
  const api=await ApiPromise.create({provider:new HttpProvider('https://testnet.flop.network/'),noInitWarn:true});
  try {
    if((await api.rpc.chain.getBlockHash(0)).toHex()!==PIN)throw Error('GENESIS_MISMATCH');
    const head=await api.rpc.chain.getFinalizedHead();
    const height=(await api.rpc.chain.getHeader(head)).number.toNumber();
    if(q.kind==='balance'){
      const at=await api.at(head);
      const {data}=await at.query.system.account(q.wallet);
      if(api.registry.chainDecimals[0]!==18||data.free===undefined||data.reserved===undefined)throw Error('ACCOUNT_SCHEMA_UNVERIFIED');
      return {ok:true,genesis:PIN,finalized:true,height,address:q.wallet,free:data.free.toString(),reserved:data.reserved.toString()};
    }
    if(q.kind==='locate_grant'){
      if(!HASH.test(q.tx_hash)||!Number.isSafeInteger(q.request_ms))throw Error('GRANT_SEARCH_INPUT');
      async function blockAt(n){
        const h=await api.rpc.chain.getBlockHash(n);
        const b=await api.rpc.chain.getBlock(h);
        if(b.block.header.number.toNumber()!==n)throw Error('BLOCK_HEIGHT_MISMATCH');
        return {h,b};
      }
      function blockTime(b){
        const t=b.block.extrinsics.find(e=>norm(e.method.section)==='timestamp'&&norm(e.method.method)==='set');
        const ms=Number(t?.method?.args?.[0]?.toString());
        if(!Number.isSafeInteger(ms)||ms<1)throw Error('HISTORICAL_TIMESTAMP_UNVERIFIED');
        return ms;
      }
      let start=q.cursor;
      if(!Number.isSafeInteger(start)||start<1){
        let lo=1,hi=height;
        while(lo<hi){
          const mid=Math.floor((lo+hi)/2);
          const {b}=await blockAt(mid);
          if(blockTime(b)<q.request_ms-30000)lo=mid+1;else hi=mid;
        }
        start=Math.max(1,lo-2);
      }
      if(start>height)return {ok:true,genesis:PIN,found:false,next_height:start};
      const stop=Math.min(height,start+23);
      for(let n=start;n<=stop;n++){
        const {h,b}=await blockAt(n);
        if(b.block.extrinsics.some(e=>e.hash.toHex()===q.tx_hash.toLowerCase()))
          return {ok:true,genesis:PIN,found:true,block_number:n,block_hash:h.toHex()};
      }
      return {ok:true,genesis:PIN,found:false,next_height:stop+1};
    }
    if(q.kind==='probe'){
      const event=api.events.computeChannel?.Settled;
      const names=event?.meta?.fields?.map(f=>norm(f.name.isSome?f.name.unwrap().toString():''));
      const ready=!!api.query.computeChannel?.channels&&!!names&&['channelid','minerpaid','validatorpaid','auditpaid'].every(n=>names.includes(n));
      return {ok:true,height,genesis:PIN,settlement_schema_ready:ready};
    }
    if(!Number.isSafeInteger(q.block_number)&&HASH.test(q.block_hash||''))q.block_number=(await api.rpc.chain.getHeader(q.block_hash)).number.toNumber();
    if(!HASH.test(q.tx_hash)||!Number.isSafeInteger(q.block_number)||q.block_number<1||q.block_number>height)throw Error('BLOCK_NOT_FINALIZED_OR_UNKNOWN');
    const h=await api.rpc.chain.getBlockHash(q.block_number);
    if(q.block_hash&&h.toHex()!==q.block_hash.toLowerCase())throw Error('BLOCK_HASH_MISMATCH');
    const block=await api.rpc.chain.getBlock(h);
    const ix=block.block.extrinsics.findIndex(x=>x.hash.toHex()===q.tx_hash.toLowerCase());
    if(ix<0)throw Error('TX_NOT_IN_FINALIZED_BLOCK');
    const at=await api.at(h);
    const events=(await at.query.system.events()).filter(r=>r.phase.isApplyExtrinsic&&r.phase.asApplyExtrinsic.toNumber()===ix);
    if(!events.some(r=>norm(r.event.section)==='system'&&norm(r.event.method)==='extrinsicsuccess'))throw Error('EXTRINSIC_NOT_SUCCESSFUL');
    const ms=(await at.query.timestamp.now()).toNumber();
    const acct=x=>api.createType('AccountId',x).toHex();
    const fields=e=>Object.fromEntries(e.meta.fields.map((f,i)=>[norm(f.name.isSome?f.name.unwrap().toString():''),e.data[i]]));
    const raw=x=>{if(x===undefined||!/^[0-9]+$/.test(x.toString()))throw Error('UNVERIFIED_AMOUNT');return BigInt(x.toString())};
    const common={ok:true,genesis:PIN,finalized:true,block_number:q.block_number,block_hash:h.toHex(),tx_hash:q.tx_hash.toLowerCase(),timestamp_ms:ms};
    if(q.kind==='grant'){
      const match=events.filter(r=>norm(r.event.section)==='balances'&&norm(r.event.method)==='transfer').filter(r=>{
        const d=fields(r.event);
        return d.from&&d.to&&d.amount&&acct(d.from)===acct(q.signer)&&acct(d.to)===acct(q.wallet)&&raw(d.amount)===BigInt(q.amount_raw);
      });
      if(match.length!==1)throw Error('GRANT_TRANSFER_NOT_ATTRIBUTED');
      return {...common,wallet:q.wallet,signer:q.signer,amount_raw:q.amount_raw};
    }
    if(q.kind!=='settlement'||!HASH.test(q.channel)||q.block_number<=q.grant_height||q.block_number<q.start_height)throw Error('SESSION_ID_OR_TIME_MISMATCH');
    const matches=events.filter(r=>norm(r.event.section)==='computechannel'&&norm(r.event.method)==='settled').filter(r=>{
      const d=fields(r.event);return d.channelid&&d.channelid.toHex()===q.channel.toLowerCase();
    });
    if(matches.length!==1)throw Error('SETTLED_EVENT_MISSING');
    const d=fields(matches[0].event);
    const minerPaid=raw(d.minerpaid), validatorPaid=raw(d.validatorpaid), auditPaid=raw(d.auditpaid);
    if(minerPaid<=0n||minerPaid+validatorPaid+auditPaid>BigInt(q.max_raw))throw Error('SETTLEMENT_OUTSIDE_BUDGET');
    // Verify the parties against actual chain storage. A closed channel may
    // remain in storage, or be available at the immediately preceding block.
    let channel=null;
    for(const a of [at,await api.at(block.block.header.parentHash)]){
      const entry=await a.query.computeChannel.channels(q.channel);
      if(entry.isSome){channel=entry.unwrap().toJSON();break;}
    }
    if(!channel||!channel.agent||!channel.miner||acct(channel.agent)!==acct(q.wallet)||acct(channel.miner)!==acct(q.miner))throw Error('CHANNEL_PARTY_MISMATCH');
    return {...common,channel:q.channel,wallet:q.wallet,miner:q.miner,miner_paid_raw:minerPaid.toString(),spent_raw:(minerPaid+validatorPaid+auditPaid).toString()};
  }finally{await api.disconnect();}
}
main().then(x=>{clearTimeout(deadline);console.log(JSON.stringify(x));process.exit(0)}).catch(e=>{clearTimeout(deadline);console.log(JSON.stringify({ok:false,code:String(e.message).match(/^[A-Z0-9_]{1,80}$/)?e.message:'CHAIN_ADAPTER_UNAVAILABLE'}));process.exit(1)});