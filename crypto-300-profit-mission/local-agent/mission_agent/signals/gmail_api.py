"""Standard-library Gmail API adapter reusing an existing authorized-user OAuth file.

No credential provisioning, OAuth consent, new scopes, secret logging or token
persistence. A connected Codex Gmail tool is not a daemon OAuth credential.
"""
import base64,json,os,time,urllib.request,urllib.error,urllib.parse
from pathlib import Path
from .gmail import CredentialBlocked,RetryableError,PermanentError,AmbiguousSend

class OAuthGmail:
    def __init__(self,credential_path,recipient=None,*,open_url=urllib.request.urlopen):
        self.path=Path(credential_path);self.recipient=recipient;self.open_url=open_url;self._token=None;self._expires=0;self.last_api_result=None
    def ready(self):
        if self._token and self._expires>time.time()+60:return
        try:
            v=json.loads(self.path.read_text());scopes=v.get('scopes',[]);scopes=scopes.split() if isinstance(scopes,str) else scopes
            allowed=set(scopes);broad={'https://mail.google.com/','https://www.googleapis.com/auth/gmail.modify'}
            if not allowed.intersection(broad) and not {'https://www.googleapis.com/auth/gmail.send','https://www.googleapis.com/auth/gmail.readonly'}<=allowed:raise CredentialBlocked('INSUFFICIENT_SCOPE')
            if v.get('token_uri','https://oauth2.googleapis.com/token') not in ('https://oauth2.googleapis.com/token','https://accounts.google.com/o/oauth2/token'):raise CredentialBlocked('TOKEN_ENDPOINT_NOT_ALLOWLISTED')
            if not all(v.get(k) for k in ('refresh_token','client_id','client_secret')):raise CredentialBlocked('EXISTING_OAUTH_UNAVAILABLE')
            data=urllib.parse.urlencode({k:v[k] for k in ('refresh_token','client_id','client_secret')}|{'grant_type':'refresh_token'}).encode()
            req=urllib.request.Request('https://oauth2.googleapis.com/token',data=data,method='POST',headers={'Content-Type':'application/x-www-form-urlencoded'})
            with self.open_url(req,timeout=8) as response:token=json.load(response)
            if not token.get('access_token'):raise CredentialBlocked('EXISTING_OAUTH_UNAVAILABLE')
            self._token=token['access_token'];self._expires=time.time()+int(token.get('expires_in',3600))
            if not self.recipient:self.recipient=self._request('GET','profile')['emailAddress']
        except (OSError,ValueError,KeyError,urllib.error.HTTPError,urllib.error.URLError):raise CredentialBlocked('EXISTING_OAUTH_UNAVAILABLE') from None
    def _request(self,method,path,body=None,*,sending=False):
        req=urllib.request.Request('https://gmail.googleapis.com/gmail/v1/users/me/'+path,data=json.dumps(body).encode() if body is not None else None,method=method,headers={'Authorization':'Bearer '+self._token,'Content-Type':'application/json'})
        try:
            with self.open_url(req,timeout=8) as response:
                value=json.load(response)
                self.last_api_result={'http_status':getattr(response,'status',200),'endpoint':method+' users/me/'+path.split('?')[0],'google_error_code':None,'google_error_reason':None,'exception_class':None}
                return value
        except urllib.error.HTTPError as exc:
            code=exc.code
            try:
                error=json.loads(exc.read()).get('error',{})
                reasons=[e.get('reason') for e in error.get('errors',[]) if e.get('reason')]
                detail={'http_status':code,'endpoint':method+' users/me/'+path.split('?')[0],'google_error_code':error.get('code',code),'google_error_reason':reasons or error.get('status'),'exception_class':type(exc).__name__}
            except (ValueError,OSError):
                detail={'http_status':code,'endpoint':method+' users/me/'+path.split('?')[0],'google_error_code':code,'google_error_reason':'UNAVAILABLE','exception_class':type(exc).__name__}
            self.last_api_result=detail
            if code in (401,403):self._token=None;raise CredentialBlocked('GMAIL_ACCESS_UNAVAILABLE') from None
            if sending and code>=500:raise AmbiguousSend('GMAIL_SEND_OUTCOME_UNCERTAIN') from None
            if code in (404,408,429) or code>=500:raise RetryableError('GMAIL_READBACK_RETRY_PENDING') from None
            raise PermanentError('GMAIL_REQUEST_REJECTED_'+str(code)) from None
        except (urllib.error.URLError,TimeoutError,OSError,ValueError):
            if sending:raise AmbiguousSend('GMAIL_SEND_OUTCOME_UNCERTAIN') from None
            raise RetryableError('GMAIL_READBACK_UNAVAILABLE') from None
    def find_sent(self,message_id,signal_id):
        # Gmail supports RFC822 Message-ID search; visible marker provides fallback.
        for q in ('in:sent rfc822msgid:'+message_id.strip('<>'),'in:sent "'+signal_id+'"'):
            ids=[];page=None
            while True:
                params={'q':q,'maxResults':100}
                if page:params['pageToken']=page
                value=self._request('GET','messages?'+urllib.parse.urlencode(params));ids.extend(x['id'] for x in value.get('messages',[]));page=value.get('nextPageToken')
                if not page:break
            if ids:return sorted(set(ids))
        return []
    def get(self,message_id):return self._request('GET','messages/'+urllib.parse.quote(message_id,safe='')+'?format=raw')
    def send(self,raw):return self._request('POST','messages/send',{'raw':base64.urlsafe_b64encode(raw).decode()},sending=True)

def existing_provider(config_path=None):
    path=os.environ.get('FRANK_GMAIL_EXISTING_OAUTH_FILE');recipient=os.environ.get('FRANK_GMAIL_RECIPIENT')
    if config_path and Path(config_path).is_file():
        try:
            config=json.loads(Path(config_path).read_text());path=config.get('existing_oauth_file',path);recipient=config.get('recipient',recipient)
        except (OSError,ValueError):return None
    return OAuthGmail(path,recipient) if path and Path(path).is_file() else None
