"""D1 fixed HTTPS guards. Entirely in-memory fake connections, never network."""
import json
from pathlib import Path
import ssl
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from f0_l2_d1_https import (_exchange_with_factory,
                           _parse_reviewed_fake_frame,send_live,HOST,PORT)

def req():
    return {"jsonrpc":"2.0","id":7,"method":"eth_blockNumber","params":[]}

class Response:
    def __init__(self,status=200,headers=None,
                 body=b'{"jsonrpc":"2.0","id":7,"result":"0x38"}'):
        self.status=status
        self.headers=headers if headers is not None else [
            ("Content-Type","application/json")]
        self.body=body
        self.read_sizes=[]
    def getheaders(self):
        return self.headers
    def read(self,n):
        self.read_sizes.append(n)
        return self.body[:n]

class Connection:
    def __init__(self,response):
        self.response=response
        self.requests=[]
        self.closed=False
    def request(self,*args,**kwargs):
        self.requests.append((args,kwargs))
    def getresponse(self):
        return self.response
    def close(self):
        self.closed=True

class Factory:
    def __init__(self,response=None):
        self.response=response if response is not None else Response()
        self.created=[]
        self.connections=[]
    def __call__(self,host,*,port,timeout,context):
        self.created.append((host,port,timeout,context))
        connection=Connection(self.response)
        self.connections.append(connection)
        return connection

class D1SealedHTTPSTests(unittest.TestCase):
    def test_unconditional_live_deny(self):
        with self.assertRaisesRegex(ValueError,"D1_LIVE_TRANSPORT_DISABLED"):
            send_live(req())
        with self.assertRaisesRegex(ValueError,"D1_LIVE_TRANSPORT_DISABLED"):
            send_live(req(),{"user_authorized":True})

    def test_strict_origin_tls_single_post_and_no_proxy(self):
        fake=Factory()
        with patch("http.client.HTTPSConnection",
                   side_effect=AssertionError("network forbidden")):
            frame=_exchange_with_factory(req(),fake,timeout_s=1.25,
                                         max_bytes=1024)
        self.assertEqual(_parse_reviewed_fake_frame(frame,req())["id"],7)
        self.assertEqual(len(fake.created),1)
        host,port,timeout,context=fake.created[0]
        self.assertEqual((host,port,timeout),(HOST,PORT,1.25))
        self.assertTrue(context.check_hostname)
        self.assertEqual(context.verify_mode,ssl.CERT_REQUIRED)
        self.assertEqual(len(fake.connections[0].requests),1)
        args,kwargs=fake.connections[0].requests[0]
        self.assertEqual(args[:2],("POST","/"))
        self.assertEqual(kwargs["headers"]["Accept-Encoding"],"identity")
        self.assertEqual(kwargs["headers"]["Host"],HOST)
        self.assertEqual(json.loads(kwargs["body"])["id"],7)
        self.assertEqual(fake.response.read_sizes,[1025])
        self.assertTrue(fake.connections[0].closed)

    def test_http_503_stored_raw_but_no_retry(self):
        fake=Factory(Response(status=503,body=b'{"error":"rate limit"}'))
        frame=_exchange_with_factory(req(),fake)
        self.assertEqual(frame[0],503)
        self.assertEqual(len(fake.connections[0].requests),1)
        with self.assertRaisesRegex(ValueError,"HTTP_STATUS_NOT_OK"):
            _parse_reviewed_fake_frame(frame,req())

    def test_redirect_does_not_follow(self):
        fake=Factory(Response(status=307,headers=[
            ("Location","https://example.org/"),
            ("Content-Type","application/json")]))
        with self.assertRaisesRegex(ValueError,"REDIRECT_FORBIDDEN"):
            _exchange_with_factory(req(),fake)
        self.assertEqual(len(fake.connections[0].requests),1)
        self.assertTrue(fake.connections[0].closed)

    def test_compression_denied(self):
        fake=Factory(Response(headers=[
            ("Content-Type","application/json"),
            ("Content-Encoding","gzip")]))
        with self.assertRaisesRegex(ValueError,"COMPRESSED_RESPONSE_FORBIDDEN"):
            _exchange_with_factory(req(),fake)
        self.assertTrue(fake.connections[0].closed)

    def test_size_cap_and_response_id(self):
        fake=Factory(Response(body=b"x"*120))
        with self.assertRaisesRegex(ValueError,"RESPONSE_SIZE_LIMIT"):
            _exchange_with_factory(req(),fake,max_bytes=100)
        self.assertEqual(fake.response.read_sizes,[101])
        wrong=Factory(Response(
            body=b'{"jsonrpc":"2.0","id":99,"result":"0x38"}'))
        with self.assertRaisesRegex(ValueError,"HTTP_RPC_IDENTITY_MISMATCH"):
            _parse_reviewed_fake_frame(_exchange_with_factory(req(),wrong),req())

    def test_invalid_config_and_params_denied(self):
        for t in (0,5.001,100):
            with self.assertRaisesRegex(ValueError,"TRANSPORT_CONFIG_INVALID"):
                _exchange_with_factory(req(),Factory(),timeout_s=t)
        with self.assertRaisesRegex(ValueError,"TRANSPORT_CONFIG_INVALID"):
            _exchange_with_factory(req(),Factory(),max_bytes=2000001)
        with self.assertRaisesRegex(ValueError,"HTTP_RPC_PARAMS_INVALID"):
            _exchange_with_factory({"jsonrpc":"2.0","id":7,
                                    "method":"eth_blockNumber",
                                    "params":[1]},Factory())

if __name__=="__main__":
    unittest.main()
