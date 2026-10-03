"""User-run Desktop OAuth bootstrap. Never activates production delivery."""
import argparse, base64, fcntl, hashlib, json, os, secrets, stat, time, uuid
import urllib.parse, urllib.request, webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from mission_agent.signals.gmail import GmailOutbox, TEST_SUBJECT
from mission_agent.signals.gmail_api import OAuthGmail
from mission_agent.signals.store import Ledger

ROOT = Path.home()/'.config/frank-local-gmail'
SCOPES = ('https://www.googleapis.com/auth/gmail.send', 'https://www.googleapis.com/auth/gmail.readonly')

class SetupError(Exception): pass

def private_root(root):
    root = Path(root)
    if root.is_symlink(): raise SetupError('UNSAFE_STORAGE_PATH')
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(root, 0o700)
    return root

def save_private(path, value):
    temp = path.with_name(path.name+'.'+secrets.token_hex(8)+'.tmp')
    fd = os.open(temp, os.O_WRONLY|os.O_CREAT|os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, 'w') as out:
            json.dump(value, out); out.flush(); os.fsync(out.fileno())
        os.replace(temp, path)
    finally:
        if temp.exists(): temp.unlink()

def load_private(path):
    if path.is_symlink() or not path.is_file() or stat.S_IMODE(path.stat().st_mode)!=0o600:
        raise SetupError('PRIVATE_FILE_REQUIRES_MODE_600')
    return json.loads(path.read_text())

def desktop_client(path):
    if not path.is_file(): raise SetupError('USER_OAUTH_ACTION_REQUIRED: DESKTOP_CLIENT_MISSING')
    value = load_private(path).get('installed', {})
    if not value.get('client_id') or not value.get('client_secret'): raise SetupError('DESKTOP_CLIENT_REQUIRED')
    if value.get('auth_uri') != 'https://accounts.google.com/o/oauth2/auth' or value.get('token_uri') != 'https://oauth2.googleapis.com/token':
        raise SetupError('GOOGLE_ENDPOINT_REQUIRED')
    return value

def authorize(client):
    verifier = secrets.token_urlsafe(64); state = secrets.token_urlsafe(32)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip('=')
    result = {}
    class Callback(BaseHTTPRequestHandler):
        def log_message(self, *args): pass
        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            valid = parsed.path == '/callback' and secrets.compare_digest(params.get('state',[''])[0],state)
            if valid: result.update(code=params.get('code',[''])[0], error=bool(params.get('error')))
            self.send_response(200 if valid else 400); self.end_headers()
            self.wfile.write(b'Authorization received. Return to your terminal.' if valid else b'Invalid OAuth callback.')
    with HTTPServer(('127.0.0.1',0),Callback) as server:
        server.timeout=1
        redirect = f'http://127.0.0.1:{server.server_port}/callback'
        query = urllib.parse.urlencode(dict(client_id=client['client_id'],redirect_uri=redirect,response_type='code',scope=' '.join(SCOPES),state=state,code_challenge=challenge,code_challenge_method='S256',access_type='offline',prompt='consent'))
        if not webbrowser.open('https://accounts.google.com/o/oauth2/v2/auth?'+query): raise SetupError('SYSTEM_BROWSER_UNAVAILABLE')
        print('USER_OAUTH_ACTION_REQUIRED: select your Google account and explicitly authorize Gmail send/read.')
        deadline=time.monotonic()+600
        while not result and time.monotonic()<deadline: server.handle_request()
    if not result.get('code') or result.get('error'): raise SetupError('USER_OAUTH_NOT_COMPLETED')
    data=urllib.parse.urlencode(dict(client_id=client['client_id'],client_secret=client['client_secret'],code=result['code'],code_verifier=verifier,redirect_uri=redirect,grant_type='authorization_code')).encode()
    with urllib.request.urlopen(urllib.request.Request('https://oauth2.googleapis.com/token', data=data),timeout=15) as response:
        token=json.load(response)
    if set(token.get('scope','').split()) != set(SCOPES) or not token.get('refresh_token'): raise SetupError('EXACT_SCOPES_AND_REFRESH_TOKEN_REQUIRED')
    return dict(type='authorized_user',client_id=client['client_id'],client_secret=client['client_secret'],refresh_token=token['refresh_token'],token_uri='https://oauth2.googleapis.com/token',scopes=list(SCOPES))

class CountingProvider(OAuthGmail):
    def __init__(self,path): super().__init__(path); self.send_count=0
    def send(self,raw): self.send_count+=1; return super().send(raw)

def verify_test(root):
    credential=root/'authorized-user.json'; load_private(credential)
    identity=root/'test-identity.json'
    if not identity.exists(): save_private(identity, {'signal_id':'test-'+str(uuid.uuid4())})
    sid=load_private(identity)['signal_id']
    ledger=Ledger(root/'setup-state.sqlite'); os.chmod(root/'setup-state.sqlite',0o600)
    try:
        box=GmailOutbox(ledger)
        box.enqueue(dict(signal_id=sid,subject=TEST_SUBJECT,body='THIS IS A DELIVERY TEST\nNOT A LIVE INVESTMENT SIGNAL\n'+sid),mode='TEST')
        provider=CountingProvider(credential); box.drain(provider,allow_test=True)
        row=box.row(sid)
        if row['status']!='SENT_VERIFIED': raise SetupError('TEST_SEND_OR_READBACK_PENDING: '+row['status'])
        ids=provider.find_sent(row['wire_message_id'],sid)
        if ids != [row['gmail_message_id']]: raise SetupError('TEST_SENT_SEARCH_REQUIRES_REVIEW')
        box.verify(row,provider.get(ids[0]))
        proof=dict(test_message_id=ids[0],signal_id=sid,initial_send_calls=provider.send_count,receipt=json.loads(row['receipt']))
        save_private(root/'test-receipt.json',proof)
        # Only the isolated TEST ledger loses local SENT state. No production row is touched.
        ledger.db.execute("UPDATE gmail_delivery SET status='SENDING',gmail_message_id=NULL,gmail_thread_id=NULL,readback_verified=0,receipt=NULL WHERE signal_id=?",(sid,))
        ledger.db.commit()
        ledger.db.close()
        ledger=Ledger(root/'setup-state.sqlite'); box=GmailOutbox(ledger)
        recovery=CountingProvider(credential); box.drain(recovery,allow_test=True)
        restored=box.row(sid)
        if recovery.send_count or restored['status']!='SENT_VERIFIED' or restored['gmail_message_id']!=ids[0]: raise SetupError('TEST_CRASH_RECOVERY_NOT_VERIFIED')
        again=CountingProvider(credential); box.drain(again,allow_test=True)
        if again.send_count: raise SetupError('TEST_DEDUPE_FAILED')
        proof.update(test_send='PASS',test_sent_readback='PASS',test_dedupe='PASS',duplicate_send_count=0,production_activated=False)
        save_private(root/'test-receipt.json',proof)
        print(json.dumps({k:v for k,v in proof.items() if k!='receipt'},sort_keys=True))
        print('OAUTH_TEST_COMPLETE: return to the current Codex chat for launchd verification and controlled Gmail activation.')
    finally: ledger.db.close()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true'); parser.add_argument('--verify',action='store_true')
    args=parser.parse_args()
    try:
        if args.check:
            desktop_client(ROOT/'oauth-desktop-client.json')
            print('DESKTOP_CLIENT=AVAILABLE; credential_backend=LOCAL_FILE; production_activated=false'); return 0
        root=private_root(ROOT)
        with (root/'setup.lock').open('a') as lock:
            os.chmod(root/'setup.lock',0o600); fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            if not (root/'authorized-user.json').exists():
                if args.verify: raise SetupError('LOCAL_CREDENTIAL_MISSING')
                save_private(root/'authorized-user.json',authorize(desktop_client(root/'oauth-desktop-client.json')))
            verify_test(root)
        return 0
    except SetupError as exc: print(str(exc)); return 2
    except Exception:
        # OAuth/HTTP errors can contain secrets. Never print exception objects or traceback.
        print('OAUTH_SETUP_BLOCKED: private setup state preserved; retry the same command.'); return 2

if __name__=='__main__': raise SystemExit(main())
