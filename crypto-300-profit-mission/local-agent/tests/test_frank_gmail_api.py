import json,urllib.parse,urllib.error
from pathlib import Path
import pytest
from mission_agent.signals.gmail_api import OAuthGmail,existing_provider
from mission_agent.signals.gmail import CredentialBlocked,RetryableError,AmbiguousSend

class Response:
    def __init__(self,value):self.value=value
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def read(self):return json.dumps(self.value).encode()

def credential(tmp_path,scopes=None):
    p=tmp_path/'existing-authorized-user.json';p.write_text(json.dumps({'refresh_token':'synthetic-refresh','client_id':'synthetic-client','client_secret':'synthetic-secret','scopes':scopes if scopes is not None else ['https://www.googleapis.com/auth/gmail.send','https://www.googleapis.com/auth/gmail.readonly']}));return p

def test_existing_oauth_reused_without_rewriting_file_or_installing_packages(tmp_path):
    p=credential(tmp_path);before=p.read_bytes();calls=[]
    def request(req,**kwargs):calls.append(req);return Response({'access_token':'synthetic-access','expires_in':3600}) if 'oauth2' in req.full_url else Response({'emailAddress':'owner@example.invalid'})
    api=OAuthGmail(p,open_url=request);api.ready();assert api.recipient=='owner@example.invalid' and len(calls)==2 and p.read_bytes()==before
    assert set(urllib.parse.parse_qs(calls[0].data.decode()))=={'refresh_token','client_id','client_secret','grant_type'}

def test_send_only_oauth_cannot_claim_sent_readback(tmp_path):
    p=credential(tmp_path,['https://www.googleapis.com/auth/gmail.send']);api=OAuthGmail(p,open_url=lambda *a,**k:pytest.fail('scope expansion attempted'))
    with pytest.raises(CredentialBlocked):api.ready()

def test_no_local_credential_is_blocked_even_if_connector_exists(tmp_path,monkeypatch):
    monkeypatch.delenv('FRANK_GMAIL_EXISTING_OAUTH_FILE',raising=False);assert existing_provider(tmp_path/'missing-config') is None

def test_message_list_searches_stable_rfc822_then_visible_marker(tmp_path):
    api=OAuthGmail(credential(tmp_path));api._token='synthetic';calls=[]
    def request(method,path,body=None,**kwargs):calls.append(path);return {'messages':[]} if len(calls)==1 else {'messages':[{'id':'existing-sent'}]}
    api._request=request;assert api.find_sent('<stable@local.invalid>','signal-identity')==['existing-sent'];assert len(calls)==2 and 'rfc822msgid' in urllib.parse.unquote(calls[0]) and 'signal-identity' in calls[1]

@pytest.mark.parametrize('sending,exception',[(False,RetryableError),(True,AmbiguousSend)])
def test_provider_failures_never_expose_secret_error_body(tmp_path,sending,exception):
    def failure(*args,**kwargs):raise urllib.error.URLError('synthetic-secret-provider-body')
    api=OAuthGmail(credential(tmp_path),open_url=failure);api._token='synthetic'
    with pytest.raises(exception) as caught:api._request('POST' if sending else 'GET','messages/send' if sending else 'messages',sending=sending)
    assert 'synthetic-secret' not in str(caught.value)
