import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

// Read-only validator for the EXISTING hourly TGE monitor. This never sends,
// creates tasks, accesses wallets, nor substitutes for actual source retrieval.
const url=x=>/^https:\/\//.test(String(x||''));
const iso=x=>Number.isFinite(Date.parse(String(x||'')));
const delta=x=>x&&typeof x==='object'
  && String(x.changed_field||'').length>=3
  && String(x.old_value||'').trim()!==String(x.new_value||'').trim()
  && String(x.old_value||'').trim().length>0
  && String(x.new_value||'').trim().length>0
  && url(x.evidence_url)
  && iso(x.evidence_published_at);
const firstPartyReceipt=r=>r&&r.status==='checked'
  && ['A','B'].includes(r.evidence_tier)
  && r.original_read===true && r.issuer_identity_verified===true
  && url(r.source_url) && iso(r.checked_at)
  && iso(r.source_published_at) && String(r.actual_status_text||'').trim().length>=25;
export function classifySourceReceipt(receipt) {
  if(firstPartyReceipt(receipt)) return 'CHECKED_ORIGINAL';
  if(receipt?.access_error||receipt?.status==='source_gap') return 'SOURCE_GAP';
  return 'PARTIAL_ONLY';
}
export function validateTgeAction(input={}) {
  const c=input.candidate||{}, errors=[],warnings=[];
  const fail=(code)=>errors.push(code);
  if(!c.project_id||!c.event_type||!c.family_key||!c.material_version||!c.event_key)
    fail('EVENT_IDENTITY_INCOMPLETE');
  if(c.identity_verified!==true||c.registry_active!==true||c.user_suppressed===true)
    fail('PROJECT_SCOPE_OR_IDENTITY_UNVERIFIED');
  const receipts=(input.source_receipts||[]).filter(x=>x.project_id===c.project_id);
  if(!receipts.some(firstPartyReceipt))fail('FIRST_PARTY_RIGHTS_RECEIPT_MISSING');
  if(!['A','B'].includes(c.evidence_tier)||!url(c.source_url)||
     c.issuer_original_read!==true)fail('DISCOVERY_ONLY_NOT_ACTION');
  if(!iso(c.source_published_at)||!iso(c.checked_at))
    fail('SOURCE_DATES_MISSING');
  if(!c.new_action_verified||!c.user_rights_relevance)
    fail('NO_NEW_USER_ACTION');
  if(c.stage==='CLAIM_ACTION' &&
     (c.official_claim_portal_verified!==true||c.action_currently_open!==true))
    fail('CLAIM_PORTAL_OR_WINDOW_UNVERIFIED');
  if(c.stage==='TGE_PREFLIGHT' &&
     (c.issuer_tge_time_verified!==true||!iso(c.event_effective_at)))
    fail('TGE_TIME_UNVERIFIED');
  const now=Date.parse(String(c.checked_at||'')),
        deadline=Date.parse(String(c.deadline_at||'')),
        start=Date.parse(String(c.event_effective_at||''));
  if(iso(c.deadline_at)&&Number.isFinite(now)&&deadline<now)
    fail('EXPIRED_ACTION');
  if(c.stage==='TGE_PREFLIGHT'&&Number.isFinite(now)&&Number.isFinite(start)
       && (start-now>72*3600000||start-now < -3600000))
    fail('PREFLIGHT_OUTSIDE_72H');
  const prior=(input.delivered_events||[]).filter(x=>x.family_key===c.family_key&&x.delivered===true);
  if(prior.some(x=>x.material_version===c.material_version))
    fail('ALREADY_DELIVERED_SAME_VERSION');
  if(prior.length && !prior.some(x=>x.material_version===c.novelty_proof?.previous_material_version &&
        delta(c.novelty_proof)))fail('OLD_EVENT_NO_VERIFIED_MATERIAL_DELTA');
  const gm=input.gmail_check||{};
  if(gm.available!==true||gm.checked_recipient!==true||gm.checked_stable_event!==true)
    fail('GMAIL_SENT_DEDUPE_UNVERIFIED');
  if(gm.already_sent===true)fail('ALREADY_SENT_GMAIL');
  if(c.user_completed===true||c.user_refunded===true||c.user_claimed===true)
    fail('USER_ACTION_ALREADY_COMPLETED');
  if(input.git_staging?.status==='failed')
    warnings.push('GIT_STAGING_FAILED_NOT_A_DELIVERY_VETO');
  if(c.user_eligibility==='UNKNOWN'&&c.stage==='TGE_PREFLIGHT')
    warnings.push('PREFLIGHT_ENTITLEMENT_UNKNOWN_LABEL_REQUIRED');
  if(c.user_eligibility==='UNKNOWN'&&c.stage==='CLAIM_ACTION')
    warnings.push('PERSONAL_ALLOCATION_UNVERIFIED_DO_NOT_CLAIM_AMOUNT');
  return {eligible:errors.length===0,decision:errors.length===0?'SEND_ELIGIBLE':'NO_ACTION_OR_UNVERIFIED',
          errors:[...new Set(errors)],warnings,source_coverage:receipts.every(firstPartyReceipt)?'CHECKED_ISSUER':'PARTIAL'};
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 if(process.argv.length!==3){process.stderr.write('Usage: node action_gate.mjs candidate_manifest.json\n');process.exitCode=2;}
 else {const v=validateTgeAction(JSON.parse(fs.readFileSync(process.argv[2],'utf8')));
   process.stdout.write(JSON.stringify(v,null,2)+'\n');process.exitCode=v.eligible?0:1;}
}
