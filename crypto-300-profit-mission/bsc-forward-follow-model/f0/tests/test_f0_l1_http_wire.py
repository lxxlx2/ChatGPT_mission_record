"""Pure offline HTTP JSON-RPC wire protocol and prospective height tests."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from f0_l1_http_wire import (
    ENDPOINT, json_body, valid_rpc_payload, parse_http_response,
    make_injected_http_sender, plan_prospective_heights,
)


def req(method='eth_getBlockByNumber', params=None, ident=3):
    if params is None:
        params=['0x64', True] if method=='eth_getBlockByNumber' else []
    return {'jsonrpc':'2.0','id':ident,'method':method,'params':params}


def response(ident=3, result=None):
    if result is None:
        result={'number':'0x64','transactions':[]}
    return {'jsonrpc':'2.0','id':ident,'result':result}


class L1HttpWireTests(unittest.TestCase):
    def test_exact_official_endpoint_and_full_transactions_serialization(self):
        payload=req()
        encoded=json_body(payload)
        self.assertEqual(json.loads(encoded),payload)
        self.assertEqual(ENDPOINT,'https://bsc-dataseed.bnbchain.org')
        self.assertNotIn(b'eth_getLogs',encoded)

    def test_wrong_methods_parameters_and_ids_rejected_before_callback(self):
        for bad in [req('eth_sendRawTransaction',[]), req(params=['0x64',False]),
                    req(params=['latest',True]), req(params=['0x064',True]),
                    req(params=['0x0',True]), req(ident=True),
                    req('eth_chainId',['unexpected'])]:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                valid_rpc_payload(bad)

    def test_fake_transport_gets_exact_bounded_post_and_returns_rpc(self):
        calls=[]
        def fake(endpoint,request_bytes,timeout,cap):
            calls.append((endpoint,json.loads(request_bytes),timeout,cap))
            return 200,{'Content-Type':'application/json; charset=utf-8'},json.dumps(response()).encode()
        sender=make_injected_http_sender(fake,max_response_bytes=4096,timeout_s=1.5)
        result=sender(req())
        self.assertEqual(result['id'],3)
        self.assertEqual(calls,[(ENDPOINT,req(),1.5,4096)])

    def test_redirect_is_never_accepted(self):
        with self.assertRaisesRegex(ValueError,'HTTP_STATUS_NOT_OK_NO_REDIRECT'):
            parse_http_response(302,{'content-type':'application/json'},b'{}',req())

    def test_large_or_empty_body_rejected(self):
        body=json.dumps(response()).encode()
        for raw,cap in [(body,8),(b'',1000)]:
            with self.subTest(raw=raw), self.assertRaisesRegex(ValueError,'HTTP_BODY_SIZE_INVALID'):
                parse_http_response(200,{'content-type':'application/json'},raw,req(),max_bytes=cap)

    def test_compressed_and_non_json_content_rejected(self):
        body=json.dumps(response()).encode()
        for headers,err in [({'Content-Type':'text/html'},'HTTP_JSON_CONTENT_TYPE_REQUIRED'),
                            ({'Content-Type':'application/json','Content-Encoding':'gzip'},
                             'HTTP_COMPRESSED_RESPONSE_REJECTED')]:
            with self.assertRaisesRegex(ValueError,err):
                parse_http_response(200,headers,body,req())

    def test_wrong_id_invalid_json_or_error_result_ambiguity_rejected(self):
        bodies=[(json.dumps(response(11)).encode(),'HTTP_RPC_IDENTITY_MISMATCH'),
                (b'{','HTTP_INVALID_JSON_RESPONSE'),
                (json.dumps({'jsonrpc':'2.0','id':3,'result':{},'error':{'code':-32000}}).encode(),
                 'HTTP_RPC_RESULT_ERROR_AMBIGUOUS')]
        for body,err in bodies:
            with self.subTest(err=err),self.assertRaisesRegex(ValueError,err):
                parse_http_response(200,{'content-type':'application/json'},body,req())

    def test_provider_error_retains_rpc_structure_but_no_network_retries(self):
        calls=[]
        def fake(url,body,timeout,cap):
            calls.append(True)
            return 200,{'content-type':'application/json'},json.dumps({
                'jsonrpc':'2.0','id':3,'error':{'code':-32000,'message':'mock-secret'}}).encode()
        result=make_injected_http_sender(fake)(req())
        self.assertEqual(result['error']['code'],-32000)
        self.assertEqual(len(calls),1)

    def test_planned_heights_are_only_prospective_not_retrospective(self):
        plan=plan_prospective_heights(
            {'jsonrpc':'2.0','id':1,'result':'0x38'},
            {'jsonrpc':'2.0','id':2,'result':'0x7aad797'},
            chain_request_id=1,head_request_id=2,max_block_reads=5)
        self.assertEqual(plan['observed_head'],128636823)
        self.assertEqual((plan['start_height'],plan['end_height']),
                         (128636824,128636828))
        self.assertEqual(plan['identity_reads_not_in_block_budget'],2)
        self.assertTrue(plan['requires_fresh_live_permission'])
        self.assertEqual(plan['actual_rpc_calls'],0)

    def test_non_bsc_wrong_head_id_or_oversized_window_rejected(self):
        for chain,head,ident,n in [
            ({'jsonrpc':'2.0','id':1,'result':'0x1'},
             {'jsonrpc':'2.0','id':2,'result':'0x64'},2,1),
            ({'jsonrpc':'2.0','id':1,'result':'0x38'},
             {'jsonrpc':'2.0','id':9,'result':'0x64'},2,1),
            ({'jsonrpc':'2.0','id':1,'result':'0x38'},
             {'jsonrpc':'2.0','id':2,'result':'0x64'},2,513)]:
            with self.assertRaises(ValueError):
                plan_prospective_heights(chain,head,chain_request_id=1,
                                         head_request_id=ident,max_block_reads=n)

    def test_injected_transport_exception_propagates_no_implicit_retry(self):
        calls=[]
        def fail(*args):
            calls.append(args)
            raise TimeoutError('synthetic')
        sender=make_injected_http_sender(fail)
        with self.assertRaises(TimeoutError):
            sender(req())
        self.assertEqual(len(calls),1)

if __name__ == '__main__':
    unittest.main()
