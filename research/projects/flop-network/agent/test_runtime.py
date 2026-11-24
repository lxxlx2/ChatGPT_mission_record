"""Offline tests: never call Gmail network, RPC or paid inference."""
import base64
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import agent
import mail
import runtime

class FakeProvider:
    def __init__(self):
        self.recipient='configured-test-user@example.invalid'
        self.messages={}
        self.count=0
    def ready(self):
        pass
    def find_sent(self, wire_id, key):
        return [i for i,x in self.messages.items()
                if x.get('key')==key]
    def send(self, raw):
        self.count+=1
        mid='gmail-test-'+str(self.count)
        self.messages[mid]={'id':mid,'labelIds':['SENT'],'raw':base64.urlsafe_b64encode(raw).decode(),
                            'key':str(__import__('email').message_from_bytes(raw)['X-Flop-Notification-Key'])}
        return {'id':mid}
    def get(self, mid):
        return self.messages[mid]

class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.conn=sqlite3.connect(str(Path(self.temp.name)/'test.sqlite3'))
        self.conn.row_factory=sqlite3.Row
        runtime.ensure_state(self.conn)
        mail.init(self.conn)
    def tearDown(self):
        self.conn.close()
        self.temp.cleanup()
    def test_mail_test_sent_readback_and_idempotent(self):
        mail.enqueue(self.conn,'first-mail-setup-test','[FLOP] 邮件通道首次验收','Offline fake mail content')
        provider=FakeProvider()
        result = mail.pump(self.conn,provider)
        if result.get('first-mail-setup-test') != 'SENT_VERIFIED':
            import email as _email
            row = self.conn.execute("SELECT * FROM flop_mail WHERE mail_key='first-mail-setup-test'").fetchone()
            item = next(iter(provider.messages.values()), None)
            if item:
                msg = _email.message_from_bytes(base64.urlsafe_b64decode(item['raw']+'==='), policy=_email.policy.default)
                body = msg.get_content().replace('\\r\\n','\\n')
                expected = row['body']+'\\n\\nFLOP-Notification-Key: '+row['mail_key']+'\\nFLOP-Content-SHA256: '+row['content_sha']+'\\n'
                print('DEBUG_MAIL_SENT', {
                    'error_code':row['error_code'],
                    'subject_ok':str(msg['Subject'])==row['subject'],
                    'key_ok':str(msg['X-Flop-Notification-Key'])==row['mail_key'],
                    'hash_ok':str(msg['X-Flop-Content-SHA256'])==row['content_sha'],
                    'body_equal':body==expected,
                    'body_length':len(body), 'expected_length':len(expected),
                    'result':result})
        self.assertEqual(result['first-mail-setup-test'],'SENT_VERIFIED')
        self.assertEqual(provider.count,1)
        self.assertEqual(mail.pump(self.conn,provider),{})
        self.assertEqual(provider.count,1)
        self.assertEqual(mail.mail_status(self.conn)['sent_verified'],1)
    def test_ambiguous_sending_never_resends(self):
        mail.enqueue(self.conn,'error-new-TEST-123','[FLOP] 异常告警｜TEST','Error captured')
        self.conn.execute("UPDATE flop_mail SET status='SENDING' WHERE mail_key='error-new-TEST-123'")
        self.conn.commit()
        p=FakeProvider()
        result=mail.pump(self.conn,p)
        self.assertEqual(result['error-new-TEST-123'],'SENT_UNVERIFIED')
        self.assertEqual(p.count,0)
    def test_bad_sent_receipt_not_marked_sent(self):
        mail.enqueue(self.conn,'first-mail-setup-test','[FLOP] 邮件测试','Test body')
        p=FakeProvider()
        def wrong_get(mid):
            x=p.messages[mid].copy()
            x['labelIds']=[]
            return x
        p.get=wrong_get
        result=mail.pump(self.conn,p)
        self.assertEqual(result['first-mail-setup-test'],'PERMANENT_ERROR')
        self.assertEqual(mail.mail_status(self.conn)['sent_verified'],0)
    def test_no_summary_outside_bangkok_slots(self):
        from zoneinfo import ZoneInfo
        frozen=datetime(2026,11,24,14,4,tzinfo=ZoneInfo('Asia/Bangkok'))
        with patch.object(runtime,'now_bkk',return_value=frozen):
            self.assertFalse(runtime.queue_summary(self.conn))
        frozen=datetime(2026,11,24,20,4,tzinfo=ZoneInfo('Asia/Bangkok'))
        with patch.object(runtime,'now_bkk',return_value=frozen):
            self.assertTrue(runtime.queue_summary(self.conn))
            self.assertFalse(runtime.queue_summary(self.conn))
    def test_planned_network_never_ready(self):
        self.assertEqual(runtime.official_testnet_state(lambda url:'Network: testnet (planned)')['status'],'PLANNED')
        self.assertFalse(runtime.official_testnet_state(lambda url:'Testnet is coming soon')['ready'])
    def test_real_first_success_requires_chain_verifier(self):
        self.conn.execute("""INSERT INTO session_attempts
              (attempt_id,phase,started_utc,wallet,expected_genesis,miner,max_flop)
              VALUES (?,?,?,?,?,?,?)""",
              ('first-live-direct','CLI_RESULT_NEEDS_CHAIN_FINALITY','2026-11-24T07:01Z','own-wallet',
               '0x'+'a'*64,'independent-miner','0.01'))
        self.conn.commit()
        evidence={'verification_authority':'CLI_RESULT',
                  'network':'testnet','genesis':'0x'+'a'*64,'payer':'own-wallet',
                  'miner':'independent-miner','verified_turns':1,'finalized':True,
                  'settlement_tx':'0x'+'b'*64,'spent_flop':'0.008'}
        with self.assertRaisesRegex(ValueError,'INDEPENDENT_VERIFIER_REQUIRED'):
            runtime.mark_first_success_from_independent_verifier(self.conn,evidence)
        self.assertEqual(mail.mail_status(self.conn)['sent_verified'],0)
        evidence['verification_authority']='DIRECT_CHAIN_VERIFIER_V1'
        evidence['payer']='another-wallet'
        with self.assertRaisesRegex(ValueError,'PARTY_MISMATCH'):
            runtime.mark_first_success_from_independent_verifier(self.conn,evidence)
        evidence['payer']='own-wallet'
        self.assertTrue(runtime.mark_first_success_from_independent_verifier(self.conn,evidence))
        row=self.conn.execute("SELECT status FROM flop_mail WHERE mail_key='first-real-test-success'").fetchone()
        self.assertEqual(row[0],'PENDING')
        fake=FakeProvider()
        res=mail.pump(self.conn,fake)
        if res.get('first-real-test-success') != 'SENT_VERIFIED':
            row=self.conn.execute("SELECT * FROM flop_mail WHERE mail_key='first-real-test-success'").fetchone()
            print('DEBUG_FIRST_SUCCESS',{'error_code':row['error_code'],'result':res,'sent_count':fake.count})
        self.assertEqual(res['first-real-test-success'],'SENT_VERIFIED')
        self.assertEqual(fake.count,1)
        self.assertFalse(runtime.mark_first_success_from_independent_verifier(self.conn,evidence))
        self.assertEqual(fake.count,1)
    def test_direct_session_prior_attempt_stops_any_retry(self):
        self.conn.execute("""INSERT INTO session_attempts
              (attempt_id,phase,started_utc,wallet,expected_genesis,miner,max_flop)
              VALUES (?,?,?,?,?,?,?)""",
              ('first-live-direct','UNKNOWN_MAY_HAVE_SUBMITTED','2026-11-24T07:01Z','w',
               '0x'+'a'*64,'m','0.01'))
        self.conn.commit()
        result=runtime.do_direct_first(self.conn,{'total_test_flop_budget':'1','max_flop':'0.01'})
        self.assertEqual(result['state'],'BLOCKED_PRIOR_ATTEMPT_RECONCILE')
    def test_email_never_reports_dollars(self):
        with patch.object(runtime,'now_bkk',return_value=datetime(2026,11,24,8,1,tzinfo=runtime.BKK)):
            runtime.queue_summary(self.conn)
        msg=self.conn.execute('SELECT body FROM flop_mail WHERE mail_key=?',('summary-2026-11-24-08',)).fetchone()[0]
        self.assertIn('未确认',msg)
        self.assertIn('已独立核验',msg)


    def test_summary_after_wake_catches_previous_bangkok_slot(self):
        mail.enqueue(self.conn,'first-mail-setup-test','[FLOP] 邮件通道首次验收','mock')
        self.conn.execute("UPDATE flop_mail SET created_at='2026-11-23T18:00:00+00:00' WHERE mail_key='first-mail-setup-test'")
        self.conn.commit()
        with patch.object(runtime,'now_bkk',return_value=datetime(2026,11,24,7,10,tzinfo=runtime.BKK)):
            self.assertFalse(runtime.queue_summary(self.conn))
        with patch.object(runtime,'now_bkk',return_value=datetime(2026,11,24,9,12,tzinfo=runtime.BKK)):
            self.assertTrue(runtime.queue_summary(self.conn))
            self.assertFalse(runtime.queue_summary(self.conn))


    def test_existing_tick_reports_dashboard_failure_by_mail(self):
        data=Path(self.temp.name)
        bind=data/'dashboard-bind.json'
        bind.write_text(json.dumps({'port':18766}))
        with patch.object(runtime,'DATA',data):
            def fail(*args,**kwargs):
                raise OSError('fixture-down')
            self.assertEqual(runtime.check_dashboard_health_from_tick(self.conn,opener=fail),
                             'DASHBOARD_UNHEALTHY')
            before=self.conn.execute("SELECT COUNT(*) FROM flop_mail WHERE subject LIKE '[FLOP] 异常告警%'").fetchone()[0]
            self.assertEqual(before,1)
            runtime.check_dashboard_health_from_tick(self.conn,opener=fail)
            after=self.conn.execute("SELECT COUNT(*) FROM flop_mail WHERE subject LIKE '[FLOP] 异常告警%'").fetchone()[0]
            self.assertEqual(after,1)
            self.assertEqual(runtime.get(self.conn,'dashboard_health'),'FAILED_OSError')
    def test_existing_tick_accepts_only_our_dashboard_identity(self):
        data=Path(self.temp.name)
        (data/'dashboard-bind.json').write_text(json.dumps({'port':18766}))
        expected={'service':'flop-dashboard','build':'flop-dashboard-dynamic-port-v3',
                  'host':'127.0.0.1','port':18766,
                  'source_path':str(Path(runtime.__file__).resolve().parent),
                  'pid':91002}
        class FakeHttp:
            status=200
            def __enter__(self):return self
            def __exit__(self,*a):return False
            def read(self,n):return json.dumps(expected).encode('utf-8')
        with patch.object(runtime,'DATA',data):
            self.assertEqual(runtime.check_dashboard_health_from_tick(
                             self.conn,opener=lambda *a,**k:FakeHttp()),
                             'HTTP_200_IDENTITY_VERIFIED')
            expected['service']='technocore-dashboard'
            self.assertEqual(runtime.check_dashboard_health_from_tick(
                             self.conn,opener=lambda *a,**k:FakeHttp()),
                             'DASHBOARD_UNHEALTHY')


    def test_planned_doc_does_not_hide_reachable_rpc_or_authorize_faucet(self):
        observed={'ready':False,'reason':'OFFICIAL_PROFILE_PLANNED',
                  'profile_status':'planned','rpc_reachable':True,
                  'observed_genesis':'0x'+'a'*64,'rpc_genesis_matches_expected':None,
                  'faucet_reachable':False,'finalized_height':42}
        with patch.object(runtime,'now',return_value=datetime(2026,11,24,15,tzinfo=timezone.utc)):
            result=runtime.ready_to_send(self.conn,fetch=lambda u:'Network: testnet (planned)',
                                        cli_status=lambda:observed)
        self.assertFalse(result['ready'])
        self.assertEqual(runtime.get(self.conn,'network_status'),'RPC_REACHABLE_AWAITING_OFFICIAL_PIN')
        self.assertEqual(runtime.get(self.conn,'observed_genesis'),'0x'+'a'*64)
        self.assertEqual(runtime.get(self.conn,'finalized_height'),'42')
        self.assertEqual(runtime.get(self.conn,'faucet_reachable'),'false')

    def test_published_doc_requires_exact_genesis_and_cli_ready(self):
        genesis='0x'+'a'*64
        document='<p>Network: testnet <b>(live)</b></p><dt>Expected genesis</dt><dd><code>'+genesis+'</code></dd><script>status: planned</script>'
        self.assertEqual(runtime.official_testnet_state(lambda u:document)['genesis'],genesis)
        self.assertFalse(runtime.official_testnet_state(lambda u:'Network: testnet (live)')['ready'])
        with patch.object(runtime,'now',return_value=datetime(2026,11,24,15,tzinfo=timezone.utc)):
            ready={'ready':True,'genesis':genesis,'rpc_reachable':True,'settlement_ready':True}
            first=runtime.ready_to_send(self.conn,fetch=lambda u:document,cli_status=lambda:ready)
            self.assertEqual(first['reason'],'PRIVATE_CONFIG_NOT_CONFIGURED')
            self.assertEqual(first['genesis'],genesis)
            ready['genesis']='0x'+'b'*64
            mismatch=runtime.ready_to_send(self.conn,fetch=lambda u:document,cli_status=lambda:ready)
            self.assertEqual(mismatch['reason'],'DOC_RPC_GENESIS_MISMATCH')
            self.assertFalse(mismatch['ready'])

    def test_cli_planned_retains_actual_rpc_and_finalized_data(self):
        genesis='0x'+'a'*64
        obj={'network':'testnet','profile_status':'planned',
             'rpc':{'url':'wss://testnet.flop.network','overridden':False,
                    'reachable':True,'genesis_hash':genesis,'matches_expected':None},
             'faucet':{'reachable':False,'ready':None,'matches_rpc':None}}
        cp=type('CP',(),{'returncode':0,'stdout':json.dumps(obj)})()
        with patch.object(runtime.shutil,'which',return_value='/fake/flop'),\
             patch.object(runtime.subprocess,'run',return_value=cp):
            out=runtime.cli_network_status(finality_probe=lambda g:{'hash':'0x'+'b'*64,'height':42})
        self.assertFalse(out['ready'])
        self.assertTrue(out['rpc_reachable'])
        self.assertEqual(out['finalized_height'],42)
        self.assertEqual(out['observed_genesis'],genesis)
        self.assertIsNone(out['rpc_genesis_matches_expected'])

    def test_finality_observation_rejects_mismatched_genesis(self):
        genesis='0x'+'a'*64
        payload={'genesis':genesis,'finalized':'0x'+'b'*64,'number':'0x2a'}
        with patch.object(runtime.shutil,'which',return_value='/fake/node'),\
             patch.object(runtime.subprocess,'run') as run:
            run.return_value=type('CP',(),{'returncode':0,'stdout':json.dumps(payload)})()
            self.assertEqual(runtime.rpc_finality_observation(genesis)['height'],42)
            self.assertIsNone(runtime.rpc_finality_observation('0x'+'c'*64))

if __name__=='__main__':
    unittest.main()
