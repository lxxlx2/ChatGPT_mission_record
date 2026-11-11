import test from 'node:test';
import assert from 'node:assert/strict';
import {validateTgeAction,classifySourceReceipt} from '../scripts/action_gate.mjs';
const base=()=>{
 const c={project_id:'cambria',event_key:'cambria:rsgp-base-tge:2026-10-29',
  family_key:'cambria:rsgp-base-tge',material_version:'2026-10-29T15:00Z',
  event_type:'TGE',stage:'TGE_PREFLIGHT',registry_active:true,identity_verified:true,
  evidence_tier:'A',source_url:'https://docs.cambria.gg/genesis/usdrsgp',
  issuer_original_read:true,source_published_at:'2026-10-27T00:00:00Z',
  checked_at:'2026-10-28T12:00:00Z',event_effective_at:'2026-10-29T15:00:00Z',
  issuer_tge_time_verified:true,new_action_verified:true,user_rights_relevance:true,
  user_eligibility:'UNKNOWN'};
 const receipt={project_id:'cambria',event_key:c.event_key,family_key:c.family_key,material_version:c.material_version,status:'checked',evidence_tier:'A',
  original_read:true,issuer_identity_verified:true,source_url:c.source_url,
  checked_at:c.checked_at,source_published_at:c.source_published_at,
  actual_status_text:'The original issuer establishes a current actionable TGE milestone and token distribution time.'};
 return {candidate:c,source_receipts:[receipt],delivered_events:[],
  gmail_check:{available:true,checked_recipient:true,checked_stable_event:true,already_sent:false},
  git_staging:{status:'ok'}};
};
test('new original-source 72h TGE preflight may alert with UNKNOWN personal allocation',()=>{
 const r=validateTgeAction(base());assert.equal(r.eligible,true,JSON.stringify(r.errors));
 assert.ok(r.warnings.includes('PREFLIGHT_ENTITLEMENT_UNKNOWN_LABEL_REQUIRED'));
});
test('SurfBoard original claim old already-delivered stable family is silent',()=>{
 const x=base(),c=x.candidate;c.project_id='surf';c.event_key='surf:surfboard_member_claim_open:2026-10-15';
 c.family_key='surf:surfboard_member_claim_open';c.material_version='2026-10-15';
 c.event_type='CLAIM';c.stage='CLAIM_ACTION';c.source_url='https://asksurf.ai/blog/en/surfboard-nft-launch';
 c.checked_at='2026-11-11T12:00:00Z';c.deadline_at='2026-11-13T23:59:00Z';
 c.official_claim_portal_verified=true;c.action_currently_open=true;
 x.source_receipts[0]={...x.source_receipts[0],project_id:'surf',event_key:c.event_key,family_key:c.family_key,material_version:c.material_version,source_url:c.source_url,checked_at:c.checked_at};
 x.delivered_events=[{family_key:c.family_key,material_version:c.material_version,delivered:true,gmail_id:'1a13e676f3e4e04d'}];
 assert.ok(validateTgeAction(x).errors.includes('ALREADY_DELIVERED_SAME_VERSION'));
});
test('StandX DUSD claim mirrored-only statement stays internal unverified',()=>{
 const x=base(),c=x.candidate;c.project_id='standx';c.event_key='standx:dusd_claim_window_open:2026-11';
 c.family_key='standx:dusd_claim_window_open';c.evidence_tier='D';
 c.issuer_original_read=false;c.source_url='https://thirdparty.example/standx-mirror';
 x.source_receipts=[{...x.source_receipts[0],project_id:'standx',event_key:c.event_key,family_key:c.family_key,material_version:c.material_version,source_url:c.source_url,
  evidence_tier:'D',original_read:false,actual_status_text:'Mirror asserts a claim; original issuer post inaccessible'}];
 assert.equal(validateTgeAction(x).eligible,false);
 assert.ok(validateTgeAction(x).errors.includes('DISCOVERY_ONLY_NOT_ACTION'));
});
test('Cambria already emailed Base TGE does not re-alert without real changed version',()=>{
 const x=base();
 x.delivered_events=[{family_key:x.candidate.family_key,material_version:x.candidate.material_version,delivered:true,gmail_id:'1a1812a1f6802ecb'}];
 assert.ok(validateTgeAction(x).errors.includes('ALREADY_DELIVERED_SAME_VERSION'));
});
test('Git staging failure does not veto first valid urgent email',()=>{
 const x=base();x.git_staging={status:'failed',error:'GITHUB_409'};
 const r=validateTgeAction(x);assert.equal(r.eligible,true,JSON.stringify(r.errors));
 assert.ok(r.warnings.includes('GIT_STAGING_FAILED_NOT_A_DELIVERY_VETO'));
});
test('unverified Gmail Sent dedupe blocks blind resend',()=>{
 const x=base();x.gmail_check.available=false;
 assert.ok(validateTgeAction(x).errors.includes('GMAIL_SENT_DEDUPE_UNVERIFIED'));
});
test('already sent Gmail wins over stale Git pending records',()=>{
 const x=base();x.gmail_check.already_sent=true;
 assert.ok(validateTgeAction(x).errors.includes('ALREADY_SENT_GMAIL'));
});
test('new material deadline with original proof may be different version',()=>{
 const x=base();x.delivered_events=[{family_key:x.candidate.family_key,material_version:'old-deadline',delivered:true}];
 x.candidate.novelty_proof={previous_material_version:'old-deadline',changed_field:'TGE_UTC',
  old_value:'2026-10-28T15:00Z',new_value:'2026-10-29T15:00Z',
  evidence_url:'https://docs.cambria.gg/genesis/usdrsgp',evidence_published_at:'2026-10-27T00:00:00Z'};
 assert.equal(validateTgeAction(x).eligible,true,JSON.stringify(validateTgeAction(x).errors));
});
test('expired original claim window is not an actionable first alert',()=>{
 const x=base();x.candidate.deadline_at='2026-10-27T10:00:00Z';
 assert.ok(validateTgeAction(x).errors.includes('EXPIRED_ACTION'));
});
test('batch search and unread original cannot claim source covered',()=>{
 const x=base().source_receipts[0];x.original_read=false;x.status='partial';
 assert.equal(classifySourceReceipt(x),'PARTIAL_ONLY');
});
test('real original issuer receipt with date and readable status is checked',()=>{
 assert.equal(classifySourceReceipt(base().source_receipts[0]),'CHECKED_ORIGINAL');
});

test('old issuer source cannot validate a different new claim event',()=>{
 const x=base();x.candidate.event_key='cambria:rsgp-new-claim:2026-11-11';
 x.candidate.family_key='cambria:rsgp-new-claim';
 x.candidate.material_version='new-claim-2026-11-11';
 x.candidate.event_type='CLAIM';x.candidate.stage='CLAIM_ACTION';
 x.candidate.official_claim_portal_verified=true;x.candidate.action_currently_open=true;
 const r=validateTgeAction(x);
 assert.equal(r.eligible,false);
 assert.ok(r.errors.includes('ISSUER_RECEIPT_NOT_BOUND_TO_CANDIDATE_VERSION'));
});
test('first-party homepage for same project cannot replace event-specific original',()=>{
 const x=base();
 x.source_receipts[0].source_url='https://cambria.gg/';
 const r=validateTgeAction(x);
 assert.ok(r.errors.includes('ISSUER_RECEIPT_NOT_BOUND_TO_CANDIDATE_VERSION'));
});
test('same exact rights event with official source remains eligible',()=>{
 const x=base(),r=validateTgeAction(x);
 assert.equal(r.eligible,true,JSON.stringify(r.errors));
});
