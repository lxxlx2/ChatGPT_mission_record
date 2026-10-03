import json, os
import pytest
from mission_agent.gmail_setup import __main__ as setup
from test_frank_gmail_delivery import Provider

def test_private_storage_permissions_and_symlink_rejection(tmp_path):
    root=setup.private_root(tmp_path/'private'); path=root/'authorized-user.json'
    setup.save_private(path,{'example':'synthetic'})
    assert (root.stat().st_mode & 0o777)==0o700
    assert (path.stat().st_mode & 0o777)==0o600
    link=tmp_path/'link'; link.symlink_to(root)
    with pytest.raises(setup.SetupError): setup.private_root(link)
    path.chmod(0o644)
    with pytest.raises(setup.SetupError): setup.load_private(path)

def test_missing_desktop_client_stops_before_browser(tmp_path):
    with pytest.raises(setup.SetupError,match='DESKTOP_CLIENT_MISSING'): setup.desktop_client(tmp_path/'absent')

def test_untrusted_client_endpoint_rejected(tmp_path):
    path=tmp_path/'client'; setup.save_private(path,{'installed':dict(client_id='synthetic',client_secret='synthetic',auth_uri='https://attacker.invalid',token_uri='https://oauth2.googleapis.com/token')})
    with pytest.raises(setup.SetupError,match='GOOGLE_ENDPOINT_REQUIRED'): setup.desktop_client(path)

def test_same_identity_recovery_and_rerun_never_resend(tmp_path,monkeypatch):
    setup.save_private(tmp_path/'authorized-user.json',{'synthetic':True})
    shared=Provider()
    class Counter:
        recipient=shared.recipient
        def __init__(self,path): self.send_count=0
        def ready(self): return shared.ready()
        def find_sent(self,*args): return shared.find_sent(*args)
        def get(self,*args): return shared.get(*args)
        def send(self,raw): self.send_count+=1; return shared.send(raw)
    monkeypatch.setattr(setup,'CountingProvider',Counter)
    setup.verify_test(tmp_path); first=json.loads((tmp_path/'test-receipt.json').read_text())
    setup.verify_test(tmp_path); second=json.loads((tmp_path/'test-receipt.json').read_text())
    assert len(shared.sent)==1
    assert first['signal_id']==second['signal_id']
    assert second['duplicate_send_count']==0 and second['production_activated'] is False
